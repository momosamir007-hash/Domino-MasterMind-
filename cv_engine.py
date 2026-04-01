"""
👁️ محرك الرؤية الحاسوبية - النسخة الشاملة والأكثر مرونة (Ultimate Digital Vision)
"""
import cv2
import numpy as np
from game_engine.tiles import Tile

class DominoVision:
    def __init__(self):
        self.TILE_WIDTH = 100
        self.TILE_HEIGHT = 200

    def process_image(self, image_bytes) -> tuple[list[Tile], np.ndarray]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        output_img = img.copy()
        
        # ─── الطبقة 1: عزل الحجارة بذكاء (Otsu's Method) ───
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # استخدام Otsu ليقوم النظام باكتشاف مستوى اللون الأبيض تلقائياً سواء كانت الصورة مظلمة أو ساطعة
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_tiles = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # نطاق مرن جداً: من الصور المقصوصة بشدة (500) إلى لقطات الشاشة 4K (500000)
            if 500 < area < 500000:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.int32(box)
                
                width = rect[1][0]
                height = rect[1][1]
                if width == 0 or height == 0: continue
                
                aspect_ratio = max(width, height) / min(width, height)
                
                # نسبة مرنة لدعم حجارة الألعاب الرقمية التي قد تكون أعرض بقليل
                if 1.2 < aspect_ratio < 3.2:
                    
                    # ─── الطبقة 2: تصحيح المنظور ───
                    warped_gray = self._warp_perspective(gray, box, width, height)
                    
                    # استخدام عتبة تكيفية (Adaptive) لقراءة النقاط بدقة حتى لو كانت رمادية أو بها ظلال
                    warped_blur = cv2.GaussianBlur(warped_gray, (3, 3), 0)
                    pip_thresh = cv2.adaptiveThreshold(warped_blur, 255, 
                                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                       cv2.THRESH_BINARY_INV, 15, 5)

                    # ─── الطبقة 3: قراءة النقاط ───
                    pips_a, pips_b = self._count_pips(pip_thresh)
                    
                    if 0 <= pips_a <= 6 and 0 <= pips_b <= 6:
                        detected_tiles.append(Tile(pips_a, pips_b))
                        
                        # رسم مربع التحديد الأخضر
                        cv2.drawContours(output_img, [box], 0, (0, 255, 0), 3)
                        center_x, center_y = int(rect[0][0]), int(rect[0][1])
                        # كتابة الرقم بلون أحمر بارز
                        cv2.putText(
                            output_img, f"{pips_a}-{pips_b}", (center_x - 30, center_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3
                        )

        output_img = cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB)
        return detected_tiles, output_img

    def _warp_perspective(self, gray_img, box, w, h):
        rect = self._order_points(box)
        dst = np.array([
            [0, 0],
            [self.TILE_WIDTH - 1, 0],
            [self.TILE_WIDTH - 1, self.TILE_HEIGHT - 1],
            [0, self.TILE_HEIGHT - 1]
        ], dtype="float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(gray_img, M, (self.TILE_WIDTH, self.TILE_HEIGHT))

    def _count_pips(self, binary_tile):
        half_h = self.TILE_HEIGHT // 2
        # قص الحجر بمسافة بادئة (Margin) بسيطة لتجنب قراءة الإطار الخارجي للحجر كنقطة
        margin = 10
        top_half = binary_tile[margin:half_h-margin, margin:self.TILE_WIDTH-margin]
        bottom_half = binary_tile[half_h+margin:self.TILE_HEIGHT-margin, margin:self.TILE_WIDTH-margin]
        return self._count_dots_in_half(top_half), self._count_dots_in_half(bottom_half)

    def _count_dots_in_half(self, half_img):
        # البحث في كل الطبقات لضمان التقاط النقاط
        contours, _ = cv2.findContours(half_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        dot_count = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # مساحة النقطة الواحدة (Pip) داخل المربع الصغير
            if 20 < area < 1500:
                # التحقق الهندسي: هل هذا الشكل عبارة عن دائرة حقاً أم خط عشوائي؟
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * (area / (perimeter * perimeter))
                    if circularity > 0.45:  # إذا كان الشكل دائرياً بنسبة 45% فما فوق فهو نقطة
                        dot_count += 1
        return min(dot_count, 6)

    def _order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect
