"""
📷 صفحة الكاميرا - مع الرؤية الحاسوبية (الطبقات الثلاث)
"""
import streamlit as st
import sys
import os

# إصلاح المسار
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from game_engine.tiles import Tile
# استيراد محرك الرؤية الذي أنشأناه للتو
from cv_engine import DominoVision 

st.set_page_config(page_title="📷 الكاميرا الذكية", page_icon="👁️", layout="wide")

st.markdown("""
<h1 style="text-align:center;
background:linear-gradient(90deg,#00d2ff,#3a7bd5);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
font-size:2em;">
👁️ كاميرا الرؤية المحسنة (X-Ray)
</h1>
<p style="text-align:center;color:#888;">
صوّر أحجارك وسيقوم النظام باستخراجها أوتوماتيكياً
</p>
""", unsafe_allow_html=True)

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📷 كاميرا حية", "📁 رفع صورة", "✏️ يدوي"])

# دالة مساعدة لمعالجة الصورة
def process_and_display(image_file):
    with st.spinner("🧠 جاري معالجة الطبقات الثلاث (حواف، قلب ألوان، مسح نقطي)..."):
        vision = DominoVision()
        bytes_data = image_file.getvalue()
        
        # استدعاء محرك الرؤية
        tiles, processed_img = vision.process_image(bytes_data)
        
        c1, c2 = st.columns(2)
        with c1:
            st.image(processed_img, caption="النظرة الآلية للمحرك (X-Ray Vision)", use_container_width=True)
            
        with c2:
            st.markdown("### 🎲 الحجارة المكتشفة:")
            if not tiles:
                st.warning("لم يتم اكتشاف حجارة واضحة. يرجى توفير إضاءة أفضل أو خلفية متباينة.")
            else:
                st.success(f"تم اكتشاف {len(tiles)} حجر بنجاح!")
                # إزالة التكرار إن وجد
                unique_tiles = list(set(tiles))
                
                cols = st.columns(4)
                for i, t in enumerate(unique_tiles):
                    with cols[i % 4]:
                        st.markdown(f"### [{t.a}|{t.b}]")
                
                if st.button("✅ حفظ هذه الحجارة في يدي", type="primary", use_container_width=True):
                    # حفظ في الجلسة للواجهة الرئيسية
                    st.session_state['hand_input'] = unique_tiles[:7] # نأخذ 7 كحد أقصى لليد
                    st.session_state['phase'] = 'setup'
                    st.toast("تم الحفظ بنجاح! انتقل للصفحة الرئيسية.", icon="✅")

with tab1:
    photo = st.camera_input("وجّه الكاميرا نحو حجارتك")
    if photo:
        process_and_display(photo)

with tab2:
    up = st.file_uploader("ارفع صورة عالية الدقة للحجارة", type=['jpg','png','jpeg'])
    if up:
        process_and_display(up)

with tab3:
    st.info("إذا فشلت الرؤية الحاسوبية بسبب الإضاءة، يمكنك الإدخال يدوياً.")
    txt = st.text_input("أحجارك (مثال: 6-4 5-5 3-1 2-0 4-3 6-6 1-0)")
    if txt:
        tiles = []
        for p in txt.strip().split():
            try:
                a, b = p.replace('|','-').split('-')
                tiles.append(Tile(int(a), int(b)))
            except: pass
        if len(tiles) > 0:
            st.success(f"✅ {len(tiles)} حجر: {tiles}")
            if st.button("🎮 استخدمها!"):
                st.session_state['hand_input'] = tiles
                st.session_state['phase'] = 'setup'
                st.toast("ارجع للصفحة الرئيسية")
