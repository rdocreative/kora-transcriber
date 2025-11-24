import os
import tempfile
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
from deepgram import DeepgramClient, PrerecordedOptions

# Configura o logging para melhor visibilidade em produção
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- Configuração ---
# Garante que a chave da API exista ao iniciar, falhando rapidamente se não estiver configurada
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    raise RuntimeError("A variável de ambiente DEEPGRAM_API_KEY não foi definida.")

# --- Modelos Pydantic ---
class ProcessRequest(BaseModel):
    session_id: str
    video_url: str

# --- Funções Auxiliares ---
def download_youtube_audio(url: str, temp_dir: str) -> str:
    """
    Baixa o áudio de uma URL do YouTube e o salva como MP3 em um diretório temporário.
    """
    output_template = os.path.join(temp_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': True,
        'nocheckcertificate': True,
    }

    logger.info(f"Iniciando download da URL: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
    
    # Encontra o arquivo .mp3 baixado no diretório temporário
    for file in os.listdir(temp_dir):
        if file.endswith('.mp3'):
            downloaded_path = os.path.join(temp_dir, file)
            logger.info(f"Download concluído. Áudio salvo em: {downloaded_path}")
            return downloaded_path
            
    raise FileNotFoundError("Não foi possível encontrar o arquivo MP3 baixado.")

async def transcribe_with_deepgram(audio_path: str) -> str:
    """
    Transcreve um arquivo de áudio usando o modelo Nova-2 da Deepgram.
    """
    try:
        dg_client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
        
        with open(audio_path, "rb") as audio_file:
            buffer_data = audio_file.read()

        payload = {'buffer': buffer_data}
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language="pt-BR" # Especificar o idioma melhora a precisão
        )

        logger.info("Enviando áudio para a Deepgram para transcrição...")
        response = await dg_client.listen.prerecorded.v("1").transcribe_file(payload, options)
        
        transcript = response.results.channels[0].alternatives[0].transcript
        logger.info("Transcrição recebida da Deepgram.")
        return transcript

    except Exception as e:
        logger.error(f"A transcrição com a Deepgram falhou: {e}")
        raise

# --- Endpoint da API ---
@app.post("/process-youtube")
async def process_youtube(req: ProcessRequest):
    """
    Endpoint principal que recebe uma URL do YouTube, baixa o áudio e o transcreve.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            logger.info(f"Processando requisição para session_id: {req.session_id}")
            
            # 1. Baixar Áudio
            audio_path = download_youtube_audio(req.video_url, temp_dir)
            
            # 2. Transcrever Áudio
            transcript = await transcribe_with_deepgram(audio_path)
            
            logger.info(f"Processado com sucesso para session_id: {req.session_id}")
            return {
                "ok": True,
                "session_id": req.session_id,
                "transcript": transcript
            }
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Erro de download para a sessão {req.session_id}: {e}")
            raise HTTPException(status_code=400, detail="Falha ao baixar o vídeo. Pode ser um vídeo privado, indisponível ou uma URL inválida.")
        except Exception as e:
            logger.error(f"Erro inesperado para a sessão {req.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno: {str(e)}")