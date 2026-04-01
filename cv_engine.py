"""
👁️ محرك الرؤية الحاسوبية - مدمج بذكاء تصفية السودوكو
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
        
        # ─── الطبقة 1: عزل الحجارة (نجحت لديك بنسبة 100%) ───
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_tiles = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 500 < area < 500000:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.int32(box)
                
                width = rect[1][0]
                height = rect[1][1]
                if width == 0 or height == 0: continue
                
                aspect_ratio = max(width, height) / min(width, height)
                if 1.2 < aspect_ratio < 3.2:
                    
                    # ─── الطبقة 2: تصحيح المنظور (Warping) ───
                    warped_gray = self._warp_perspective(gray, box, width, height)

                    # ─── الطبقة 3: قراءة النقاط (باستخدام تقنيات السودوكو) ───
                    pips_a, pips_b = self._count_pips(warped_gray)
                    
                    if 0 <= pips_a <= 6 and 0 <= pips_b <= 6:
                        # فلترة الحجارة الفارغة تماماً التي قد تكون مجرد أزرار في الشاشة
                        if pips_a == 0 and pips_b == 0 and area < 5000:
                            continue
                            
                        detected_tiles.append(Tile(pips_a, pips_b))
                        
                        cv2.drawContours(output_img, [box], 0, (0, 255, 0), 3)
                        center_x, center_y = int(rect[0][0]), int(rect[0][1])
                        
                        # خلفية سوداء للنص ليكون واضحاً
                        text = f"{pips_a}-{pips_b}"
                        cv2.rectangle(output_img, (center_x - 40, center_y - 25), (center_x + 40, center_y + 10), (0, 0, 0), -1)
                        cv2.putText(
                            output_img, text, (center_x - 35, center_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3
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

    def _count_pips(self, gray_tile):
        """تقسيم الحجر وتمرير الصور الرمادية للعد"""
        half_h = self.TILE_HEIGHT // 2
        top_half = gray_tile[0:half_h, 0:self.TILE_WIDTH]
        bottom_half = gray_tile[half_h:self.TILE_HEIGHT, 0:self.TILE_WIDTH]
        
        return self._count_dots_in_half(top_half), self._count_dots_in_half(bottom_half)

    def _count_dots_in_half(self, gray_half):
        """العد باستخدام تقنيات تنظيف السودوكو"""
        h_cell, w_cell = gray_half.shape
        
        # 1. Multi-Thresholding: استخدام Otsu لقلب الألوان بدقة (النقاط السوداء تصبح بيضاء)
        _, binary = cv2.threshold(gray_half, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        
        # 2. إزالة التشويش النقطي باستخدام Morphological Opening (من سكريبت السودوكو الخاص بك)
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # البحث عن الكنتورات
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        dot_count = 0
        for c in contours:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)
            
            # 3. استبعاد الكنتورات التي تلامس حواف الخلية (بقايا خط المنتصف الأسود وإطار الحجر) - تقنية السودوكو!
            margin = 5
            if x < margin or y < margin or (x + w) > w_cell - margin or (y + h) > h_cell - margin:
                continue
                
            # 4. فلترة المساحة والأبعاد
            if 15 < area < (h_cell * w_cell * 0.4):
                aspect_ratio = w / float(h)
                # النقطة يجب أن تكون شبه دائرية (نسبة الطول للعرض قريبة من 1)
                if 0.5 < aspect_ratio < 2.0: 
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
