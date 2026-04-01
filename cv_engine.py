"""
👁️ محرك الرؤية الحاسوبية - مهيأ خصيصاً للقطات الشاشة (Digital Screenshots)
"""
import cv2
import numpy as np
from game_engine.tiles import Tile

class DominoVision:
    def __init__(self):
        # توحيد حجم الحجر بعد قصه ليسهل عد النقاط داخله
        self.TILE_WIDTH = 100
        self.TILE_HEIGHT = 200

    def process_image(self, image_bytes) -> tuple[list[Tile], np.ndarray]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        output_img = img.copy()
        
        # ─── الطبقة 1: عزل الحجارة عن الشاشة ───
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # التعديل السحري للألعاب الرقمية:
        # الحجارة في الشاشة لونها أبيض ساطع (قيمتها فوق 220)
        # لذلك سنجعل أي شيء أبيض يظهر ناصعاً، وأي شيء آخر (كالطاولة الخضراء) يختفي تماماً
        _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_tiles = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # شاشات الهواتف دقتها عالية، لذا وسعنا نطاق المساحة المسموحة لتشمل الحجارة الكبيرة
            if 3000 < area < 200000:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.int32(box) # تم إصلاح مشكلة numpy هنا
                
                width = rect[1][0]
                height = rect[1][1]
                if width == 0 or height == 0: continue
                
                # التحقق من أن الشكل مستطيل يشبه الدومينو لمنع التقاط أزرار اللعبة
                aspect_ratio = max(width, height) / min(width, height)
                if 1.5 < aspect_ratio < 2.7:
                    
                    # ─── الطبقة 2: تصحيح المنظور ───
                    warped_gray = self._warp_perspective(gray, box, width, height)
                    
                    # قلب الألوان لقراءة النقاط: النقاط السوداء تصبح بيضاء
                    _, binary_tile = cv2.threshold(warped_gray, 120, 255, cv2.THRESH_BINARY_INV)

                    # ─── الطبقة 3: قراءة النقاط ───
                    pips_a, pips_b = self._count_pips(binary_tile)
                    
                    if 0 <= pips_a <= 6 and 0 <= pips_b <= 6:
                        # التحقق من أن الحجر ليس فارغاً تماماً بسبب خطأ
                        # (في حال التقط مربعاً أبيض لا يحتوي على أي نقاط، نعتبره 0-0 ولكن بحذر)
                        detected_tiles.append(Tile(pips_a, pips_b))
                        
                        # رسم مربع التحديد
                        cv2.drawContours(output_img, [box], 0, (0, 255, 0), 4)
                        center_x, center_y = int(rect[0][0]), int(rect[0][1])
                        cv2.putText(
                            output_img, f"{pips_a}-{pips_b}", (center_x - 30, center_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4
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
        top_half = binary_tile[0:half_h, 0:self.TILE_WIDTH]
        bottom_half = binary_tile[half_h:self.TILE_HEIGHT, 0:self.TILE_WIDTH]
        return self._count_dots_in_half(top_half), self._count_dots_in_half(bottom_half)

    def _count_dots_in_half(self, half_img):
        contours, _ = cv2.findContours(half_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        dot_count = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # مساحة النقاط (Pips) تختلف حسب الدقة، وضعنا نطاقاً مرناً
            if 15 < area < 3000: 
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
