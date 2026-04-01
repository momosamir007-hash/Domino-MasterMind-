import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game_engine.tiles import Tile

st.set_page_config(page_title="📷 الكاميرا", page_icon="📷", layout="wide")

st.markdown("## 📷 كاميرا الدومينو")
tab1, tab2, tab3 = st.tabs(["📷 كاميرا", "📁 رفع", "✏️ يدوي"])

with tab1:
    photo = st.camera_input("صوّر أحجارك")
    if photo:
        st.image(photo, use_container_width=True)
        st.info("أدخل الأحجار يدوياً في تبويب ✏️")

with tab2:
    up = st.file_uploader("ارفع صورة", type=['jpg','png','jpeg'])
    if up:
        st.image(up, use_container_width=True)

with tab3:
    txt = st.text_input("أحجارك (مثال: 6-4 5-5 3-1 2-0 4-3 6-6 1-0)")
    if txt:
        tiles = []
        for p in txt.strip().split():
            try:
                a, b = p.replace('|','-').split('-')
                tiles.append(Tile(int(a), int(b)))
            except:
                pass
        if tiles:
            st.success(f"✅ {len(tiles)} حجر: {tiles}")
            if len(tiles) == 7:
                if st.button("🎮 استخدمها!"):
                    if 'hand_input' in st.session_state:
                        st.session_state['hand_input'] = tiles
                        st.session_state['phase'] = 'setup'
                    st.success("ارجع للصفحة الرئيسية")
