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

# Transcrição de áudio
def transcribe_audio(file_path):
    result = model.transcribe(file_path)
    return result["text"]

# Transcrição de vídeo
def transcribe_video(file_path):
    audio_path = "temp_audio.mp3"
    os.system(f"ffmpeg -i {file_path} -q:a 0 -map a {audio_path}")
    transcription = transcribe_audio(audio_path)
    os.remove(audio_path)
    return transcription

# Baixar áudio do YouTube
def download_youtube_video(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'youtube_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
    return "youtube_audio.mp3"

# Baixar arquivo do Google Drive
def download_google_drive_file(url):
    file_id = url.split("/d/")[1].split("/")[0]
    output_path = "google_drive_file.mp4"
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)
    return output_path

# Salvar transcrição em formatos diferentes
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
st.set_page_config(page_title="Transcrição Inteligente", page_icon="🎙️")
st.title("🎙️ Bem-vindo ao Áudio Transcript")
st.sidebar.title("Configurações")


# Escolha do modo
mode = st.sidebar.radio(
    "Escolha o modo de entrada:",
    ["Arquivo", "YouTube", "Google Drive"],
    index=0,
    help="Selecione a origem dos seus arquivos ou links para transcrição.",
)

transcription = ""

if mode == "Arquivo":
    st.subheader("📂 Upload de Arquivo")
    uploaded_file = st.file_uploader(
        "Faça upload de um arquivo (áudio ou vídeo):", type=["mp3", "wav", "mp4", "m4a"]
    )
    if uploaded_file:
        st.success("Arquivo carregado com sucesso! Clique no botão para iniciar a transcrição.")
        if st.button("Iniciar Transcrição"):
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
    st.subheader("🎥 Link do YouTube")
    youtube_url = st.text_input("Insira o link do vídeo do YouTube:")
    if youtube_url:
        st.success("Link recebido! Clique no botão para iniciar a transcrição.")
        if st.button("Iniciar Transcrição"):
            try:
                with st.spinner("Baixando e transcrevendo o áudio..."):
                    audio_file = download_youtube_video(youtube_url)
                    transcription = transcribe_audio(audio_file)
                st.success("Transcrição concluída!")
                st.text_area("Transcrição:", transcription, height=200)
            except Exception as e:
                st.error(f"Erro ao processar o vídeo do YouTube: {e}")

elif mode == "Google Drive":
    st.subheader("📁 Link do Google Drive")
    drive_url = st.text_input("Insira o link do arquivo no Google Drive:")
    if drive_url:
        st.success("Link recebido! Clique no botão para iniciar a transcrição.")
        if st.button("Iniciar Transcrição"):
            try:
                with st.spinner("Baixando e transcrevendo o arquivo..."):
                    file_path = download_google_drive_file(drive_url)
                    transcription = transcribe_video(file_path)
                st.success("Transcrição concluída!")
                st.text_area("Transcrição:", transcription, height=200)
            except Exception as e:
                st.error(f"Erro ao processar o link do Google Drive: {e}")

# Opções de salvamento
if transcription:
    with st.expander("💾 Salvar Transcrição"):
        col1, col2 = st.columns(2)
        with col1:
            file_path = save_as_txt(transcription)
            st.download_button(
                label="Baixar TXT",
                data=open(file_path, "r", encoding="utf-8").read(),
                file_name=file_path,
                mime="text/plain",
            )
        with col2:
            file_path = save_as_word(transcription)
            st.download_button(
                label="Baixar Word",
                data=open(file_path, "rb").read(),
                file_name=file_path,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

if st.button("Reiniciar Aplicativo"):
    st.experimental_rerun()
