import os
import streamlit as st
import gdown
from pydub.utils import which
from pydub import AudioSegment
from docx import Document
import whisper
import yt_dlp
import warnings

# Suprimir avisos do Whisper
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Configurar o caminho do FFmpeg
AudioSegment.converter = which("ffmpeg")

# Carregar o modelo Whisper
model = whisper.load_model("base")

# Funções de transcrição e manipulação de arquivos
def transcribe_audio(file_path):
    result = model.transcribe(file_path)
    return result["text"]

def transcribe_video(file_path):
    audio_path = "temp_audio.mp3"
    os.system(f"ffmpeg -i {file_path} -q:a 0 -map a {audio_path}")
    transcription = transcribe_audio(audio_path)
    os.remove(audio_path)
    return transcription

def download_youtube_video(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'youtube_audio.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
    return "youtube_audio.mp3"

def download_google_drive_file(url):
    file_id = url.split("/d/")[1].split("/")[0]
    output_path = "google_drive_file.mp4"
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)
    return output_path

def save_as_txt(text, filename="transcription.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename

def save_as_word(text, filename="transcription.docx"):
    doc = Document()
    doc.add_paragraph(text)
    doc.save(filename)
    return filename

# Configuração do Streamlit
st.set_page_config(page_title="Transcrição Inteligente", page_icon="🎙️", layout="centered")

# Configuração de estilo clean e responsivo
st.markdown("""
    <style>
        body {
            font-family: 'Arial', sans-serif;
        }
        .stButton button {
            background-color: #007BFF !important;
            color: #FFFFFF !important;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        .stTextInput, .stFileUploader, .stTextArea {
            background-color: #F8F9FA !important;
            border: 1px solid #DDD !important;
            border-radius: 4px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar: Configurações principais
st.sidebar.title("🎙️ Configurações")
mode = st.sidebar.radio(
    "Escolha o modo:",
    ["Arquivo", "YouTube", "Google Drive"],
    help="Selecione o tipo de entrada para transcrição.",
)

if st.sidebar.button("🔄 Reiniciar Aplicativo"):
    # Reiniciar o aplicativo ajustando os parâmetros de URL
    st.query_params.clear()
    st.rerun()

# Interface principal
st.title("🎙️ Transcrição Inteligente")
st.write("Converta áudios e vídeos em texto de forma rápida e eficiente.")

transcription = ""

if mode == "Arquivo":
    st.subheader("📂 Upload de Arquivo")
    uploaded_file = st.file_uploader("Carregue seu arquivo de áudio ou vídeo:", type=["mp3", "wav", "mp4", "m4a"])
    if uploaded_file:
        if st.button("▶️ Iniciar Transcrição"):
            with st.spinner("Transcrevendo..."):
                file_type = uploaded_file.type
                with open("temp_file", "wb") as f:
                    f.write(uploaded_file.read())
                transcription = (
                    transcribe_audio("temp_file") if "audio" in file_type else transcribe_video("temp_file")
                )
            st.success("Transcrição concluída!")
            st.text_area("Transcrição:", transcription, height=200)

elif mode == "YouTube":
    st.subheader("🎥 Transcrição do YouTube")
    youtube_url = st.text_input("Insira o link do vídeo:")
    if youtube_url and st.button("▶️ Iniciar Transcrição"):
        try:
            with st.spinner("Baixando e transcrevendo o áudio..."):
                audio_file = download_youtube_video(youtube_url)
                transcription = transcribe_audio(audio_file)
            st.success("Transcrição concluída!")
            st.text_area("Transcrição:", transcription, height=200)
        except Exception as e:
            st.error(f"Erro ao processar o vídeo do YouTube: {e}")

elif mode == "Google Drive":
    st.subheader("📁 Transcrição do Google Drive")
    drive_url = st.text_input("Insira o link do arquivo:")
    if drive_url and st.button("▶️ Iniciar Transcrição"):
        try:
            with st.spinner("Baixando e transcrevendo o arquivo..."):
                file_path = download_google_drive_file(drive_url)
                transcription = transcribe_video(file_path)
            st.success("Transcrição concluída!")
            st.text_area("Transcrição:", transcription, height=200)
        except Exception as e:
            st.error(f"Erro ao processar o arquivo do Google Drive: {e}")

# Opções de salvamento
if transcription:
    st.subheader("💾 Salvar Transcrição")
    col1, col2 = st.columns(2)
    with col1:
        file_path = save_as_txt(transcription)
        st.download_button(
            label="📄 Baixar TXT",
            data=open(file_path, "r", encoding="utf-8").read(),
            file_name=file_path,
            mime="text/plain",
        )
    with col2:
        file_path = save_as_word(transcription)
        st.download_button(
            label="📝 Baixar Word",
            data=open(file_path, "rb").read(),
            file_name=file_path,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
