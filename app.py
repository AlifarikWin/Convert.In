import streamlit as st
import os
import asyncio
import uuid
import io
import zipfile
import base64
import speech_recognition as sr
from pydub import AudioSegment
from PIL import Image, ImageOps, ImageEnhance
from pypdf import PdfReader
import edge_tts
from pdf2docx import Converter
import docx
import streamlit_antd_components as sac
import fitz 
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip
# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AIO Converter Pro", layout="wide")

# --- 2. CUSTOM CSS (ULTRA CLEAN - NO ICONS) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; font-family: 'Inter', sans-serif; }
    .workspace-card {
        background-color: #ffffff; padding: 3rem; border-radius: 0px;
        border-top: 1px solid #f1f5f9; margin-top: 1rem;
    }
    .stButton > button {
        background-color: #000000; color: #ffffff; font-weight: 500; 
        border-radius: 4px; border: none; padding: 0.6rem 2rem; transition: 0.2s;
        letter-spacing: 0.5px;
    }
    .stButton > button:hover { background-color: #262626; color: #ffffff; }
    .header-title { color: #000000; font-weight: 700; font-size: 1.8rem; letter-spacing: -0.5px; }
    .header-sub { color: #737373; font-size: 1rem; margin-top: 0.5rem; margin-bottom: 2.5rem; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Menghapus border default streamlit file uploader agar lebih clean */
    .stFileUploader { border: 1px dashed #e5e5e5; border-radius: 8px; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI PREVIEW PDF ---
def preview_pdf(pdf_bytes):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border: 1px solid #f1f5f9; border-radius: 4px;"></iframe>'
    st.markdown("---")
    st.markdown("<p style='font-weight:600; font-size:0.9rem; color:#171717;'>PRATINJAU DOKUMEN</p>", unsafe_allow_html=True)
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- FUNGSI HEADER UI (CLEAN TEXT) ---
def ui_header(title, subtitle):
    st.markdown(f'<div class="header-title">{title.upper()}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="header-sub">{subtitle}</div>', unsafe_allow_html=True)

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h3 style='text-align: center; color: #000000; font-weight: 800; letter-spacing: 1px;'>AIO CONVERTER</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #737373; font-size: 0.8rem; margin-bottom: 30px;'>PRO EDITION</p>", unsafe_allow_html=True)
    
    selected_menu = sac.menu([
        sac.MenuItem('DOCUMENT STUDIO', icon='file-earmark-text', children=[
            sac.MenuItem('PDF ke Word'),
            sac.MenuItem('Word ke PDF'),
            sac.MenuItem('PPT ke PDF'),
            sac.MenuItem('Foto ke PDF'),
        ]),
        sac.MenuItem('AI VOICE GENERATOR', icon='mic'),
        sac.MenuItem('MEDIA TO TEXT', icon='chat-left-text'),
        sac.MenuItem('VIDEO TO AUDIO', icon='film'),
        sac.MenuItem('IMAGE STUDIO', icon='image', children=[
            sac.MenuItem('Resizer & Format'),
            sac.MenuItem('Foto Scanner Efek'),
        ]),
        sac.MenuItem('FILE ARCHIVER (ZIP)', icon='archive'),
        sac.MenuItem('SMART COMPRESSOR', icon='arrows-collapse'),
    ], open_all=True, size='sm', variant='light')

# --- 5. WORKSPACE LOGIC ---
_, col_main, _ = st.columns([1, 7, 1])

with col_main:
    with st.container():
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)

        # ==========================================
        # DOCUMENT STUDIO
        # ==========================================
        if selected_menu == 'PDF ke Word':
            ui_header("PDF ke Word", "Ekstrak konten PDF menjadi dokumen Word yang dapat diedit sepenuhnya.")
            f = st.file_uploader("Pilih file PDF", type=["pdf"])
            if f and st.button("PROSES KONVERSI"):
                uid = str(uuid.uuid4()); t_pdf, t_docx = f"i_{uid}.pdf", f"o_{uid}.docx"
                try:
                    with open(t_pdf, "wb") as file: file.write(f.getbuffer())
                    cv = Converter(t_pdf); cv.convert(t_docx); cv.close()
                    with open(t_docx, "rb") as res: 
                        doc_bytes = res.read()
                        st.success("Konversi selesai.")
                        st.download_button("UNDUH WORD (DOCX)", doc_bytes, file_name="AIO_Word.docx")
                finally:
                    for temp in [t_pdf, t_docx]: 
                        if os.path.exists(temp): os.remove(temp)

        elif selected_menu == 'Word ke PDF':
            ui_header("Word ke PDF", "Ubah dokumen Word menjadi PDF standar industri.")
            f = st.file_uploader("Pilih file Word", type=["docx"])
            if f and st.button("PROSES KONVERSI"):
                uid = str(uuid.uuid4()); t_docx, t_pdf = os.path.abspath(f"i_{uid}.docx"), os.path.abspath(f"o_{uid}.pdf")
                try:
                    import pythoncom; from docx2pdf import convert; pythoncom.CoInitialize()
                    with open(t_docx, "wb") as file: file.write(f.getbuffer())
                    convert(t_docx, t_pdf)
                    with open(t_pdf, "rb") as res: 
                        pdf_bytes = res.read(); st.success("Konversi selesai."); preview_pdf(pdf_bytes)
                        st.download_button("UNDUH PDF", pdf_bytes, file_name="AIO_Document.pdf")
                except Exception as e: st.error("Layanan konversi Word hanya tersedia di mode lokal.")
                finally:
                    for temp in [t_docx, t_pdf]:
                        if os.path.exists(temp): os.remove(temp)

        elif selected_menu == 'PPT ke PDF':
            ui_header("PowerPoint ke PDF", "Konversi slide presentasi Anda menjadi dokumen PDF.")
            f = st.file_uploader("Pilih file PowerPoint", type=["pptx", "ppt"])
            if f and st.button("PROSES KONVERSI"):
                uid = str(uuid.uuid4()); t_ppt, t_pdf = os.path.abspath(f"in_{uid}.pptx"), os.path.abspath(f"out_{uid}.pdf")
                try:
                    import pythoncom, win32com.client
                    with open(t_ppt, "wb") as file: file.write(f.getbuffer())
                    pythoncom.CoInitialize(); powerpoint = win32com.client.Dispatch("Powerpoint.Application")
                    deck = powerpoint.Presentations.Open(t_ppt, WithWindow=False)
                    deck.SaveAs(t_pdf, 32); deck.Close(); powerpoint.Quit()
                    with open(t_pdf, "rb") as res: 
                        pdf_bytes = res.read(); st.success("Konversi selesai."); preview_pdf(pdf_bytes)
                        st.download_button("UNDUH PDF", pdf_bytes, file_name="AIO_Presentation.pdf")
                except Exception as e: st.error("Layanan konversi PPT hanya tersedia di mode lokal.")
                finally:
                    for temp in [t_ppt, t_pdf]:
                        if os.path.exists(temp): os.remove(temp)

        elif selected_menu == 'Foto ke PDF':
            ui_header("Foto ke PDF", "Gabungkan berbagai citra gambar menjadi satu berkas PDF.")
            img_files = st.file_uploader("Pilih foto (JPG/PNG)", type=["jpg", "png"], accept_multiple_files=True)
            if img_files and st.button("GABUNGKAN KE PDF"):
                img_list = [Image.open(f).convert("RGB") for f in img_files]
                if img_list:
                    buf = io.BytesIO()
                    img_list[0].save(buf, format="PDF", save_all=True, append_images=img_list[1:])
                    pdf_bytes = buf.getvalue(); st.success("PDF berhasil disusun."); preview_pdf(pdf_bytes)
                    st.download_button("UNDUH PDF", pdf_bytes, file_name="AIO_Photos.pdf")

        # ==========================================
        # AI VOICE & TRANSCRIPTION
        # ==========================================
        elif selected_menu == 'AI VOICE GENERATOR':
            ui_header("AI Voice Generator", "Sintesis teks dokumen menjadi narasi audio manusia.")
            f = st.file_uploader("Pilih dokumen teks", type=["pdf", "docx"])
            if f:
                v = st.selectbox("Model Suara:", ["id-ID-ArdiNeural", "id-ID-GadisNeural"])
                if st.button("PROSES AUDIO"):
                    txt = " ".join([p.extract_text() for p in PdfReader(f).pages]) if f.type == "application/pdf" else " ".join([p.text for p in docx.Document(f).paragraphs])
                    uid = str(uuid.uuid4()); a_out = f"a_{uid}.mp3"
                    try:
                        asyncio.run(edge_tts.Communicate(txt[:2500], v).save(a_out))
                        with open(a_out, "rb") as audio:
                            aud_bytes = audio.read(); st.success("Audio selesai diproses."); st.audio(aud_bytes)
                            st.download_button("UNDUH MP3", aud_bytes, "AIO_Voice.mp3")
                    finally:
                        if os.path.exists(a_out): os.remove(a_out)

        elif selected_menu == 'MEDIA TO TEXT':
            ui_header("Media to Text", "Transkripsi otomatis dari berkas audio atau video menjadi teks.")
            f = st.file_uploader("Pilih berkas media", type=["mp3", "wav", "mp4", "mov"])
            if f:
                lang = st.selectbox("Bahasa Sumber:", [("id-ID", "Indonesia"), ("en-US", "English")])
                if st.button("MULAI TRANSKRIPSI"):
                    uid = str(uuid.uuid4()); t_in, t_wav = f"in_{uid}", f"out_{uid}.wav"
                    try:
                        with open(t_in, "wb") as file: file.write(f.getbuffer())
                        if f.type.startswith("video"):
                            clip = VideoFileClip(t_in); clip.audio.write_audiofile(t_wav, logger=None); clip.close()
                        else:
                            AudioSegment.from_file(t_in).export(t_wav, format="wav")
                        r = sr.Recognizer()
                        with sr.AudioFile(t_wav) as source: res_txt = r.recognize_google(r.record(source), language=lang[0])
                        st.success("Transkripsi selesai."); st.text_area("HASIL TEKS", res_txt, height=250)
                        st.download_button("UNDUH TEKS (.TXT)", res_txt, "AIO_Transcript.txt")
                    except Exception as e: st.error(f"Gagal memproses transkripsi: {e}")
                    finally:
                        for temp in [t_in, t_wav]:
                            if os.path.exists(temp): os.remove(temp)

        # ==========================================
        # MULTIMEDIA TOOLS
        # ==========================================
        elif selected_menu == 'VIDEO TO AUDIO':
            ui_header("Video to Audio", "Ekstraksi audio murni dari berkas video.")
            f = st.file_uploader("Pilih video", type=["mp4", "mov", "avi"])
            if f and st.button("EKSTRAK AUDIO"):
                uid = str(uuid.uuid4()); t_v, t_a = os.path.abspath(f"v_{uid}.mp4"), os.path.abspath(f"a_{uid}.mp3")
                try:
                    with open(t_v, "wb") as file: file.write(f.getbuffer())
                    clip = VideoFileClip(t_v); clip.audio.write_audiofile(t_a, logger=None); clip.close()
                    with open(t_a, "rb") as res: 
                        aud_bytes = res.read(); st.success("Ekstraksi selesai."); st.audio(aud_bytes)
                        st.download_button("UNDUH MP3", aud_bytes, "AIO_Extracted.mp3")
                finally:
                    for temp in [t_v, t_a]:
                        if os.path.exists(temp): os.remove(temp)

        elif selected_menu == 'Resizer & Format':
            ui_header("Image Resizer", "Ubah dimensi fisik dan format enkoder gambar.")
            f = st.file_uploader("Pilih gambar", type=["jpg", "png", "jpeg"])
            if f:
                img = Image.open(f); w = st.number_input("Lebar (px):", value=img.size[0]); fmt = st.selectbox("Format:", ["PNG", "JPEG"])
                if st.button("PROSES GAMBAR"):
                    h = int(img.size[1] * (w / img.size[0])); res = img.resize((w, h), Image.LANCZOS)
                    buf = io.BytesIO(); res.save(buf, format=fmt); st.success("Pemrosesan selesai.")
                    st.image(res, caption="HASIL PEMROSESAN"); st.download_button("UNDUH GAMBAR", buf.getvalue(), f"AIO_Resized.{fmt.lower()}")

        elif selected_menu == 'Foto Scanner Efek':
            ui_header("Scanner Efek", "Simulasi hasil pemindaian dokumen fisik pada foto.")
            f = st.file_uploader("Pilih foto dokumen", type=["jpg", "png", "jpeg"])
            if f and st.button("TERAPKAN EFEK"):
                img = ImageOps.grayscale(Image.open(f))
                img = ImageEnhance.Contrast(img).enhance(2.0); img = ImageEnhance.Brightness(img).enhance(1.2)
                buf = io.BytesIO(); img.save(buf, format="JPEG"); st.success("Filter diterapkan.")
                st.image(img); st.download_button("UNDUH HASIL SCAN", buf.getvalue(), "AIO_Scanned.jpg")

        # ==========================================
        # ARCHIVER & COMPRESSOR
        # ==========================================
        elif selected_menu == 'FILE ARCHIVER (ZIP)':
            ui_header("File Archiver", "Penggabungan beberapa berkas menjadi satu arsip terkompresi.")
            files = st.file_uploader("Pilih berkas", accept_multiple_files=True)
            if files and st.button("BUAT ARSIP ZIP"):
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED) as zf:
                    for file in files: zf.writestr(file.name, file.getvalue())
                st.success("Arsip berhasil dibuat."); st.download_button("UNDUH ARSIP (.ZIP)", buf.getvalue(), "AIO_Archive.zip")

        elif selected_menu == 'SMART COMPRESSOR':
            ui_header("Smart Compressor", "Reduksi ukuran berkas tanpa menghilangkan informasi krusial.")
            f = st.file_uploader("Pilih berkas", type=["jpg", "jpeg", "png", "pdf"])
            if f and st.button("MULAI KOMPRESI"):
                if "image" in f.type:
                    img = Image.open(f).convert("RGB"); buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=50); st.success("Kompresi gambar selesai.")
                    st.image(img); st.download_button("UNDUH GAMBAR", buf.getvalue(), "AIO_Compressed.jpg")
                else:
                    doc = fitz.open(stream=f.read(), filetype="pdf"); buf = io.BytesIO()
                    doc.save(buf, garbage=4, deflate=True); pdf_bytes = buf.getvalue()
                    st.success("Kompresi PDF selesai."); preview_pdf(pdf_bytes)
                    st.download_button("UNDUH PDF", pdf_bytes, "AIO_Compressed.pdf")


        st.markdown('</div>', unsafe_allow_html=True)
