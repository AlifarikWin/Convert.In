import streamlit as st
import os
import asyncio
from PIL import Image
from pypdf import PdfReader
import edge_tts
from pdf2docx import Converter
import docx
from streamlit_option_menu import option_menu

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Convert.In", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS (SaaS UI) ---
st.markdown("""
    <style>
    /* Latar belakang & Font */
    .stApp { background-color: #f4f7f6; font-family: 'Inter', sans-serif; }
    
    /* Tombol Utama (Gradient & Hover) */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white; font-weight: bold; border-radius: 10px; border: none;
        padding: 0.7rem 2rem; width: 100%; transition: 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-3px); box-shadow: 0 8px 15px rgba(124, 58, 237, 0.3); color: white;
    }
    
    /* Tombol Download Khusus */
    .stDownloadButton > button {
        background: #10B981; /* Hijau Sukses */
    }
    .stDownloadButton > button:hover {
        background: #059669; box-shadow: 0 8px 15px rgba(16, 185, 129, 0.3);
    }

    /* Card Layout untuk Area Kerja */
    .workspace-card {
        background-color: white; padding: 2rem; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e5e7eb;
        margin-top: 1rem;
    }

    /* Menyembunyikan header/footer bawaan Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION MODERN ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #4F46E5; margin-bottom: 20px;'>✨ AIO Tools</h2>", unsafe_allow_html=True)
    
    # Menggunakan option_menu yang baru saja kamu instal
    selected_menu = option_menu(
        menu_title=None, 
        options=["Document Converter", "AI Voice Generator", "Image Studio", "Smart Compressor"],
        icons=["file-earmark-text", "mic", "image", "arrows-collapse"], 
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#64748b", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#e2e8f0", "color": "#334155"},
            "nav-link-selected": {"background-color": "#4F46E5", "color": "white", "icon-color": "white"},
        }
    )
    
    st.markdown("---")
    st.caption("🚀 Version 1.0 ( Beta )")

# --- 4. AREA KERJA UTAMA (Tengah Layar) ---
# Menggunakan kolom agar konten tidak terlalu melebar (Floating Layout)
_, col_main, _ = st.columns([1, 6, 1])

with col_main:
    # Header Dinamis sesuai Menu
    st.markdown(f"<h1 style='text-align: center; color: #1e293b; font-weight: 800;'>{selected_menu}</h1>", unsafe_allow_html=True)
    
    # Bungkus dalam Card Putih
    with st.container():
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        
        # ==========================================
        # 1. DOCUMENT ENGINE
        # ==========================================
        if selected_menu == "Document Converter":
            st.markdown("<p style='text-align: center; color: #64748b;'>Ubah file PDF menjadi Word (DOCX) yang bisa diedit rapi.</p>", unsafe_allow_html=True)
            doc_file = st.file_uploader("Drop file PDF di sini", type=["pdf"], key="doc")
            
            # Progressive Disclosure: Hanya muncul jika ada file
            if doc_file:
                st.success(f"📁 Siap diproses: **{doc_file.name}**")
                st.markdown("---")
                if st.button("✨ Mulai Konversi ke Word"):
                    with st.spinner("Menyusun ulang teks dan halaman..."):
                        temp_pdf = "temp.pdf"
                        temp_docx = "output.docx"
                        with open(temp_pdf, "wb") as f: f.write(doc_file.getbuffer())
                        
                        cv = Converter(temp_pdf)
                        cv.convert(temp_docx)
                        cv.close()
                        
                        with open(temp_docx, "rb") as f:
                            st.download_button("⬇️ Download Word (DOCX)", f, file_name="AIO_Converted.docx")

        # ==========================================
        # 2. SPEECH SYNTHESIS
        # ==========================================
        elif selected_menu == "AI Voice Generator":
            st.markdown("<p style='text-align: center; color: #64748b;'>Ubah teks dokumen (PDF/Word) menjadi suara manusia natural.</p>", unsafe_allow_html=True)
            speech_file = st.file_uploader("Drop dokumen di sini", type=["pdf", "docx"], key="voice")
            
            if speech_file:
                st.success(f"📁 Siap dibaca: **{speech_file.name}**")
                st.markdown("---")
                
                # Pengaturan muncul setelah upload
                voice_style = st.selectbox("Pilih Karakter Suara AI:", ["id-ID-ArdiNeural (Pria)", "id-ID-GadisNeural (Wanita)"])
                
                if st.button("🎙️ Generate Audio Sekarang"):
                    with st.spinner("AI sedang membaca dokumenmu..."):
                        text = ""
                        if speech_file.type == "application/pdf":
                            reader = PdfReader(speech_file)
                            text = "".join([page.extract_text() for page in reader.pages])
                        elif "wordprocessingml" in speech_file.type:
                            doc = docx.Document(speech_file)
                            text = "\n".join([para.text for para in doc.paragraphs])
                        
                        if text.strip():
                            audio_out = "speech_output.mp3"
                            v_short = voice_style.split(" ")[0]
                            communicate = edge_tts.Communicate(text[:2000], v_short) 
                            asyncio.run(communicate.save(audio_out))
                            
                            st.audio(audio_out)
                            with open(audio_out, "rb") as f:
                                st.download_button("⬇️ Download MP3", f, file_name="AIO_Audiobook.mp3")
                        else:
                            st.error("Gagal membaca teks. Pastikan file bukan hasil foto/scan.")

        # ==========================================
        # 3. MEDIA PROCESSING
        # ==========================================
        elif selected_menu == "Image Studio":
            st.markdown("<p style='text-align: center; color: #64748b;'>Ubah dimensi (Pixel) dan ganti format gambar (JPG/PNG).</p>", unsafe_allow_html=True)
            media_file = st.file_uploader("Drop Gambar di sini", type=["jpg", "png", "jpeg"], key="media")
            
            if media_file:
                img = Image.open(media_file)
                st.markdown("---")
                
                col1, col2 = st.columns([1, 1.5], gap="large")
                with col1:
                    st.image(media_file, caption=f"Asli: {img.size[0]} x {img.size[1]} px", use_container_width=True)
                
                with col2:
                    st.write("**Pengaturan Output:**")
                    new_width = st.number_input("Target Lebar (Pixel):", value=img.size[0], step=100)
                    format_out = st.selectbox("Ubah Format Ke:", ["PNG", "JPEG"])
                    
                    if st.button("🎨 Proses Gambar"):
                        w_perc = (new_width / float(img.size[0]))
                        h_size = int((float(img.size[1]) * float(w_perc)))
                        img_res = img.resize((int(new_width), h_size), Image.Resampling.LANCZOS)
                        
                        if format_out == "JPEG" and img_res.mode in ("RGBA", "P"):
                            img_res = img_res.convert("RGB")
                            
                        out_name = f"AIO_Rescaled.{format_out.lower()}"
                        img_res.save(out_name, format_out)
                        
                        st.success(f"✅ Dimensi baru: {new_width} x {h_size} px")
                        with open(out_name, "rb") as f:
                            st.download_button(f"⬇️ Download {format_out}", f, file_name=out_name)

        # ==========================================
        # 4. COMPRESSION LOGIC
        # ==========================================
        elif selected_menu == "Smart Compressor":
            st.markdown("<p style='text-align: center; color: #64748b;'>Kecilkan ukuran file (MB ke KB) agar mudah dikirim tanpa pecah.</p>", unsafe_allow_html=True)
            comp_file = st.file_uploader("Drop Gambar untuk dikompres", type=["jpg", "jpeg", "png"], key="comp")
            
            if comp_file:
                st.success(f"📁 Siap dikompres: **{comp_file.name}**")
                st.markdown("---")
                
                quality_val = st.slider("Kualitas Visual (%)", 10, 100, 60, help="Semakin kecil angka, file semakin ringan.")
                
                if st.button("🗜️ Mulai Kompresi"):
                    img_c = Image.open(comp_file)
                    if img_c.mode in ("RGBA", "P"): img_c = img_c.convert("RGB")
                        
                    out_comp = "AIO_Compressed.jpg"
                    img_c.save(out_comp, "JPEG", optimize=True, quality=quality_val)
                    
                    old_size = comp_file.size / 1024 
                    new_size = os.path.getsize(out_comp) / 1024 
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Ukuran Asli", f"{old_size:.1f} KB")
                    col_m2.metric("Ukuran Baru", f"{new_size:.1f} KB", f"-{old_size - new_size:.1f} KB")
                    
                    with open(out_comp, "rb") as f:
                        st.download_button("⬇️ Download Hasil Kompresi", f, file_name="AIO_Compressed.jpg")
        
        st.markdown('</div>', unsafe_allow_html=True)