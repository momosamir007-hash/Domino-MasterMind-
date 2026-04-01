"""
👁️ محرك الرؤية الحاسوبية - قراءة الحجارة باستخدام OpenCV
يعتمد على 3 طبقات: استخراج الحواف، تصحيح المنظور وقلب الألوان، وعد النقاط.
"""
import cv2
import numpy as np
from game_engine.tiles import Tile

class DominoVision:
    def __init__(self):
        # إعدادات أبعاد الحجر المستطيل المثالي بعد قصه
        self.TILE_WIDTH = 100
        self.TILE_HEIGHT = 200

    def process_image(self, image_bytes) -> tuple[list[Tile], np.ndarray]:
        """
        تستقبل بايتات الصورة، وتعيد:
        1. قائمة بكائنات Tile المكتشفة.
        2. صورة المعاينة (التي توضح ما رآه النظام).
        """
        # تحويل البايتات إلى مصفوفة OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # نسخة للرسم عليها وعرضها للمستخدم
        output_img = img.copy()
        
        # ─── الطبقة 1: تحديد الحواف واستخراج الحجارة ───
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # العتبة التكيفية لعزل الحجارة عن الطاولة (تفترض وجود تباين)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # البحث عن الحواف (Contours)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_tiles = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # فلترة المساحات الصغيرة (الضوضاء) والمساحات الضخمة جداً
            if 2000 < area < 50000:
                # الحصول على المستطيل المائل الذي يحيط بالحجر
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.int32(box)
                
                # حساب العرض والطول للتحقق من أن الشكل يشبه مستطيل الدومينو (النسبة تقريباً 1:2)
                width = rect[1][0]
                height = rect[1][1]
                if width == 0 or height == 0: continue
                
                aspect_ratio = max(width, height) / min(width, height)
                if 1.5 < aspect_ratio < 2.5: # نسبة طول الدومينو لعرضه
                    
                    # ─── الطبقة 2: تصحيح المنظور وقلب الألوان ───
                    warped_gray = self._warp_perspective(gray, box, width, height)
                    
                    # قلب الألوان: نجعل النقاط بيضاء والخلفية سوداء
                    # نستخدم Otsu's thresholding
                    _, binary_tile = cv2.threshold(
                        warped_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
                    )

                    # ─── الطبقة 3: قراءة النقاط ───
                    pips_a, pips_b = self._count_pips(binary_tile)
                    
                    # إذا كانت القراءة منطقية (من 0 إلى 6)
                    if 0 <= pips_a <= 6 and 0 <= pips_b <= 6:
                        detected_tiles.append(Tile(pips_a, pips_b))
                        
                        # رسم مربع أخضر حول الحجر المكتشف وكتابة الأرقام عليه
                        cv2.drawContours(output_img, [box], 0, (0, 255, 0), 3)
                        center_x = int(rect[0][0])
                        center_y = int(rect[0][1])
                        cv2.putText(
                            output_img, f"{pips_a}-{pips_b}", (center_x - 20, center_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3
                        )

        # تحويل الصورة الناتجة من BGR إلى RGB لتعرض بشكل صحيح في Streamlit
        output_img = cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB)
        return detected_tiles, output_img

    def _warp_perspective(self, gray_img, box, w, h):
        """تصحيح المنظور لجعل الحجر المائل مستطيلاً أفقياً أو عمودياً مثالياً"""
        # ترتيب النقاط هندسياً (أعلى يسار، أعلى يمين، أسفل يمين، أسفل يسار)
        rect = self._order_points(box)
        
        # تحديد الأبعاد المثالية
        dst = np.array([
            [0, 0],
            [self.TILE_WIDTH - 1, 0],
            [self.TILE_WIDTH - 1, self.TILE_HEIGHT - 1],
            [0, self.TILE_HEIGHT - 1]
        ], dtype="float32")

        # مصفوفة التحويل
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(gray_img, M, (self.TILE_WIDTH, self.TILE_HEIGHT))
        return warped

    def _count_pips(self, binary_tile):
        """الطبقة 3: تقسيم الحجر لنصفين وعد النقاط (الدوائر البيضاء)"""
        # قص الحجر إلى نصفين (مربع علوي ومربع سفلي)
        half_h = self.TILE_HEIGHT // 2
        top_half = binary_tile[0:half_h, 0:self.TILE_WIDTH]
        bottom_half = binary_tile[half_h:self.TILE_HEIGHT, 0:self.TILE_WIDTH]

        return self._count_dots_in_half(top_half), self._count_dots_in_half(bottom_half)

    def _count_dots_in_half(self, half_img):
        """عد النقاط في النصف المربع بناءً على المساحة"""
        contours, _ = cv2.findContours(half_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        dot_count = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # مساحة النقطة الواحدة تقريبياً في صورة حجمها 100x100
            if 50 < area < 800: 
                # يمكن إضافة شرط التحقق من الدائرية (Circularity) لزيادة الدقة
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0: continue
                circularity = 4 * np.pi * (area / (perimeter * perimeter))
                if circularity > 0.6: # الدائرة المثالية = 1
                    dot_count += 1
        return min(dot_count, 6) # أقصى عدد لنقاط الدومينو في جهة واحدة هو 6

    def _order_points(self, pts):
        """ترتيب زوايا المربع الأربع بشكل صحيح"""
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect
