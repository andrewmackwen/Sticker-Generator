import streamlit as st
import pandas as pd
import os
import io
import tempfile
import json

# محاولة استيراد المكتبات الخارجية بحذر
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    from reportlab.graphics import renderPDF
    from svglib.svglib import svg2rlg
    import barcode
    from barcode.writer import SVGWriter
except ImportError as e:
    st.error(f"Error loading libraries: {e}. Please check requirements.txt")

# ==========================================
# 1. Auth System
# ==========================================
KEYS_FILE = 'auth_keys.json'
ADMIN_KEY = 'admin_master_2026'

def load_keys():
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'w') as f:
            json.dump({'users': []}, f)
    with open(KEYS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {'users': []}

def save_keys(data):
    with open(KEYS_FILE, 'w') as f:
        json.dump(data, f)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# ==========================================
# 2. Vector PDF Engine
# ==========================================
def generate_pdf(dataframe):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(12.5 * cm, 7.5 * cm))
    
    for index, row in dataframe.iterrows():
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(6.25 * cm, 6.3 * cm, "PPK")
        
        barcode_val = str(row['Barcode']).strip()
        if len(barcode_val) < 12:
            barcode_val = barcode_val.zfill(12)
        elif len(barcode_val) > 12:
            barcode_val = barcode_val[:12]
            
        UPC = barcode.get_barcode_class('upc')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp_svg:
            UPC(barcode_val, writer=SVGWriter()).write(tmp_svg)
            tmp_svg_path = tmp_svg.name
            
        drawing = svg2rlg(tmp_svg_path)
        drawing.scale(1.8, 1.8)
        renderPDF.draw(drawing, c, 2.5 * cm, 3.2 * cm) 
        if os.path.exists(tmp_svg_path):
            os.remove(tmp_svg_path)
        
        c.setFont("Helvetica", 10)
        c.drawString(1.0 * cm, 2.5 * cm, f"STYLE#: {row.get('Style', '')}")
        c.drawString(1.0 * cm, 2.0 * cm, f"COLOR: {row.get('Color', '')}")
        
        c.setFont("Helvetica", 9)
        c.drawString(1.0 * cm, 1.5 * cm, "SIZE / RATIO :")
        
        sx = 4.0 * cm
        c.drawString(sx, 1.5 * cm, str(row.get('Size1', '')))
        c.drawString(sx + 1.2*cm, 1.5 * cm, str(row.get('Size2', '')))
        c.drawString(sx + 2.4*cm, 1.5 * cm, str(row.get('Size3', '')))
        
        c.drawString(sx + 0.3*cm, 1.0 * cm, str(row.get('Ratio1', '')))
        c.drawString(sx + 1.5*cm, 1.0 * cm, str(row.get('Ratio2', '')))
        c.drawString(sx + 2.7*cm, 1.0 * cm, str(row.get('Ratio3', '')))
        
        c.setFont("Helvetica", 10)
        c.drawString(9.5 * cm, 2.5 * cm, f"DIM: {row.get('Dim', '')}")
        c.drawString(9.5 * cm, 2.0 * cm, f"LABEL: {row.get('Label', '')}")
        
        c.showPage()
        
    c.save()
    buffer.seek(0)
    return buffer

# ==========================================
# 3. UI
# ==========================================
def login_screen():
    st.title("🔐 نظام تصميم الاستيكرات")
    key_input = st.text_input("أدخل مفتاح الدخول:", type="password")
    if st.button("تسجيل الدخول"):
        keys_data = load_keys()
        if key_input == ADMIN_KEY:
            st.session_state.logged_in = True
            st.session_state.is_admin = True
            st.rerun()
        elif key_input in keys_data['users']:
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            st.rerun()
        else:
            st.error("خطأ!")

def main_app():
    st.title("🖨️ مولد استيكرات (Vector)")
    if st.session_state.is_admin:
        st.sidebar.title("Admin")
        keys_data = load_keys()
        nk = st.sidebar.text_input("New Key:")
        if st.sidebar.button("Add"):
            keys_data['users'].append(nk)
            save_keys(keys_data)
            st.rerun()
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    f = st.file_uploader("Upload CSV", type=['csv'])
    if f:
        df = pd.read_csv(f)
        if st.button("Generate"):
            buf = generate_pdf(df)
            st.download_button("Download PDF", buf, "labels.pdf")

if not st.session_state.logged_in: login_screen()
else: main_app()
