import streamlit as st
import os
import asyncio
import uuid
import io
import zipfile
import speech_recognition as sr
from pydub import AudioSegment
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from pypdf import PdfReader
import edge_tts
from pdf2docx import Converter
import docx
import streamlit_antd_components as sac
import fitz 
from moviepy import VideoFileClip

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AIO Converter Pro", page_icon="🚀", layout="wide")

# --- 2. CUSTOM CSS (UI MODERN) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    .workspace-card {
        background-color: white; padding: 2.5rem; border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-top: 1rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white; font-weight: 600; border-radius: 12px; border: none;
        padding: 0.6rem 2rem; transition: all 0.3s;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4); }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION (NESTED MENU) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #4F46E5; font-weight: 800;'>✨ AIO TOOLS</h2>", unsafe_allow_html=True)
    
    selected_menu = sac.menu([
        sac.MenuItem('Document Studio', icon='file-earmark-text', children=[
            sac.MenuItem('PDF ke Word', icon='filetype-docx'),
            sac.MenuItem('Word ke PDF', icon='filetype-pdf'),
        ]),
        sac.MenuItem('AI Voice Generator', icon='mic'),
        sac.MenuItem('Media to Text', icon='chat-left-text-fill'),
        sac.MenuItem('Video to Audio', icon='film'),
        sac.MenuItem('Image Studio', icon='image', children=[
            sac.MenuItem('Resizer & Format', icon='aspect-ratio'),
            sac.MenuItem('Foto Scanner Efek', icon='filter-square'),
        ]),
        sac.MenuItem('File Archiver (ZIP)', icon='archive'),
        sac.MenuItem('Smart Compressor', icon='arrows-collapse'),
    ], open_all=True, size='sm')
    
    st.markdown("---")
    st.caption("🔥 Developer Mode | Version 1.9")

# --- 4. WORKSPACE LOGIC ---
_, col_main, _ = st.columns([1, 8, 1])

with col_main:
    st.markdown(f"<h1 style='text-align: center; color: #1e293b; font-weight: 800;'>{selected_menu}</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)

        # ==========================================
        # 4.1 DOCUMENT STUDIO
        # ==========================================
        if selected_menu == 'PDF ke Word':
            f = st.file_uploader("Upload PDF", type=["pdf"])
            if f and st.button("🚀 Konversi Sekarang"):
                uid = str(uuid.uuid4())
                t_pdf, t_docx = f"i_{uid}.pdf", f"o_{uid}.docx"
                try:
                    with open(t_pdf, "wb") as file: file.write(f.getbuffer())
                    cv = Converter(t_pdf); cv.convert(t_docx); cv.close()
                    with open(t_docx, "rb") as res: st.download_button("⬇️ Download Word", res, file_name="Hasil_Konversi.docx")
                finally:
                    for temp in [t_pdf, t_docx]: 
                        if os.path.exists(temp): os.remove(temp)

        elif selected_menu == 'Word ke PDF':
            f = st.file_uploader("Upload Word (DOCX)", type=["docx"])
            if f and st.button("🚀 Konversi Sekarang"):
                uid = str(uuid.uuid4())
                t_docx, t_pdf = os.path.abspath(f"i_{uid}.docx"), os.path.abspath(f"o_{uid}.pdf")
                try:
                    import pythoncom; from docx2pdf import convert; pythoncom.CoInitialize()
                    with open(t_docx, "wb") as file: file.write(f.getbuffer())
                    convert(t_docx, t_pdf)
                    with open(t_pdf, "rb") as res: st.download_button("⬇️ Download PDF", res, file_name="Hasil_Konversi.pdf")
                finally:
                    for temp in [t_docx, t_pdf]:
                        if os.path.exists(temp): os.remove(temp)

        # ==========================================
        # 4.2 AI VOICE & TRANSCRIPTION
        # ==========================================
        elif selected_menu == 'AI Voice Generator':
            f = st.file_uploader("Upload Dokumen (PDF/DOCX)", type=["pdf", "docx"])
            if f:
                v = st.selectbox("Pilih Suara:", ["id-ID-ArdiNeural (Pria)", "id-ID-GadisNeural (Wanita)"])
                if st.button("🎙️ Generate Audio"):
                    txt = ""
                    if f.type == "application/pdf":
                        txt = " ".join([p.extract_text() for p in PdfReader(f).pages])
                    else:
                        txt = " ".join([p.text for p in docx.Document(f).paragraphs])
                    
                    uid = str(uuid.uuid4())
                    a_out = f"a_{uid}.mp3"
                    try:
                        asyncio.run(edge_tts.Communicate(txt[:2500], v.split(" ")[0]).save(a_out))
                        with open(a_out, "rb") as audio:
                            st.audio(audio.read())
                            st.download_button("⬇️ Download MP3", audio, "AIO_Voice.mp3")
                    finally:
                        if os.path.exists(a_out): os.remove(a_out)

        elif selected_menu == 'Media to Text':
            st.info("🎙️ Mendukung MP3, WAV, MP4, dan MOV.")
            f = st.file_uploader("Upload Media", type=["mp3", "wav", "mp4", "mov"])
            if f:
                lang = st.selectbox("Bahasa:", [("id-ID", "Indonesia"), ("en-US", "English")])
                if st.button("📝 Mulai Transkripsi"):
                    with st.spinner("Sedang memproses..."):
                        uid = str(uuid.uuid4())
                        t_in, t_wav = f"in_{uid}", f"out_{uid}.wav"
                        try:
                            with open(t_in, "wb") as file: file.write(f.getbuffer())
                            # Konversi ke WAV agar bisa dibaca SpeechRecognition
                            if f.type.startswith("video"):
                                clip = VideoFileClip(t_in); clip.audio.write_audiofile(t_wav, logger=None); clip.close()
                            else:
                                AudioSegment.from_file(t_in).export(t_wav, format="wav")
                            
                            r = sr.Recognizer()
                            with sr.AudioFile(t_wav) as source:
                                res_txt = r.recognize_google(r.record(source), language=lang[0])
                            
                            st.text_area("Hasil Transkripsi:", res_txt, height=200)
                            st.download_button("⬇️ Download Teks", res_txt, "transkripsi.txt")
                        except Exception as e: st.error(f"Error: {e}")
                        finally:
                            for temp in [t_in, t_wav]:
                                if os.path.exists(temp): os.remove(temp)

        # ==========================================
        # 4.3 MULTIMEDIA TOOLS
        # ==========================================
        elif selected_menu == 'Video to Audio':
            f = st.file_uploader("Upload Video", type=["mp4", "mov", "avi"])
            if f and st.button("🎵 Ekstrak Audio"):
                uid = str(uuid.uuid4())
                t_v, t_a = os.path.abspath(f"v_{uid}.mp4"), os.path.abspath(f"a_{uid}.mp3")
                try:
                    with open(t_v, "wb") as file: file.write(f.getbuffer())
                    clip = VideoFileClip(t_v)
                    clip.audio.write_audiofile(t_a, logger=None); clip.close()
                    with open(t_a, "rb") as res: st.audio(res.read()); st.download_button("⬇️ Download MP3", res, "Audio_Ekstrak.mp3")
                finally:
                    for temp in [t_v, t_a]:
                        if os.path.exists(temp): os.remove(temp)

        elif selected_menu == 'Resizer & Format':
            f = st.file_uploader("Upload Gambar", type=["jpg", "png", "jpeg"])
            if f:
                img = Image.open(f)
                w = st.number_input("Lebar Baru (Pixel):", value=img.size[0])
                fmt = st.selectbox("Format Output:", ["PNG", "JPEG"])
                if st.button("🎨 Proses Gambar"):
                    h = int(img.size[1] * (w / img.size[0]))
                    res = img.resize((w, h), Image.LANCZOS)
                    buf = io.BytesIO()
                    res.save(buf, format=fmt)
                    st.download_button("⬇️ Download", buf.getvalue(), f"AIO_Resized.{fmt.lower()}")

        elif selected_menu == 'Foto Scanner Efek':
            f = st.file_uploader("Upload Foto Dokumen", type=["jpg", "png", "jpeg"])
            if f and st.button("🪄 Terapkan Efek Scan"):
                img = ImageOps.grayscale(Image.open(f))
                img = ImageEnhance.Contrast(img).enhance(2.0)
                img = ImageEnhance.Brightness(img).enhance(1.2)
                buf = io.BytesIO(); img.save(buf, format="JPEG")
                st.image(img); st.download_button("⬇️ Download", buf.getvalue(), "Hasil_Scan.jpg")

        # ==========================================
        # 4.4 ARCHIVER & COMPRESSOR
        # ==========================================
        elif selected_menu == 'File Archiver (ZIP)':
            files = st.file_uploader("Pilih Banyak File", accept_multiple_files=True)
            if files and st.button("📦 Bungkus ke ZIP"):
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED) as zf:
                    for file in files: zf.writestr(file.name, file.getvalue())
                st.download_button("⬇️ Download ZIP", buf.getvalue(), "Arsip_AIO.zip")

        elif selected_menu == 'Smart Compressor':
            f = st.file_uploader("Upload Image/PDF", type=["jpg", "jpeg", "png", "pdf"])
            if f and st.button("🗜️ Kompres Sekarang"):
                if "image" in f.type:
                    img = Image.open(f).convert("RGB")
                    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=50)
                    st.download_button("⬇️ Download Image", buf.getvalue(), "Compressed.jpg")
                else:
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    buf = io.BytesIO(); doc.save(buf, garbage=4, deflate=True)
                    st.download_button("⬇️ Download PDF", buf.getvalue(), "Compressed.pdf")

        st.markdown('</div>', unsafe_allow_html=True)