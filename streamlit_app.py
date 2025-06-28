import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import io
# ATUALIZAÇÃO: Importa a biblioteca para gravação de áudio, removendo ClientSettings
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np

# --- Configuração da Página e API ---
st.set_page_config(
    page_title="Verificador de Golpes com IA",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configura a API do Gemini usando a chave guardada nos segredos do Streamlit
try:
    if "google_api" in st.secrets and "key" in st.secrets["google_api"]:
        genai.configure(api_key=st.secrets["google_api"]["key"])
    else:
        st.error("A configuração da chave de API do Google não foi encontrada nos segredos.")
        st.stop()
except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao configurar a API do Google. Erro: {e}")
    st.stop()

# --- Armazenamento do áudio gravado ---
if "audio_buffer" not in st.session_state:
    st.session_state["audio_buffer"] = {}

# --- Funções dos Agentes de IA ---

def transcribe_audio_to_text(audio_bytes: bytes, filename: str) -> str:
    """
    Envia bytes de áudio para o Gemini e retorna a transcrição.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = "Transcreva o seguinte áudio para texto. Retorne apenas o texto transcrito, sem nenhum outro comentário."
    
    try:
        # Envia os bytes do áudio diretamente
        audio_file = genai.upload_file(contents=audio_bytes, mime_type="audio/wav")
        response = model.generate_content([prompt, audio_file])
        
        if not response.parts:
            return f"Erro: A resposta da transcrição foi bloqueada. Razão: {response.prompt_feedback.block_reason.name}"
        return response.text
    except Exception as e:
        print(f"Erro na transcrição de áudio: {e}")
        return f"Erro ao processar o áudio: {e}"


def call_analyzer_agent(prompt_parts: list) -> dict:
    """
    Chama o Agente 1 (Gemini 1.5 Flash) para uma análise multimodal.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")

    full_prompt = ["Você é um especialista em cibersegurança (Agente Analisador). Analise o seguinte conteúdo... Sua tarefa é retornar APENAS um objeto JSON..."] + prompt_parts
    try:
        response = model.generate_content(full_prompt, generation_config=generation_config, safety_settings=safety_settings)
        if not response.parts:
             return {"error": "A resposta foi bloqueada.", "details": f"Razão do bloqueio: {response.prompt_feedback.block_reason.name}"}
        return json.loads(response.text)
    except Exception as e:
        return {"error": "Ocorreu um erro inesperado ao contactar a IA.", "details": str(e)}


def call_validator_agent(analysis_from_agent_1: dict) -> str:
    """
    Chama o Agente 2 (Gemini 1.5 Flash) para validar e formatar a resposta final.
    """
    if "error" in analysis_from_agent_1: return f"Ocorreu um erro na análise inicial. Detalhes: {analysis_from_agent_1.get('details', '')}"
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    fontes_prompt_section = '3. Uma seção "Fontes Consultadas pelo Analista" com as URLs.' if analysis_from_agent_1.get("fontes", []) else ""
    prompt = f"""Você é um especialista em comunicação de cibersegurança... Um analista júnior forneceu o seguinte JSON:\n---\n{json.dumps(analysis_from_agent_1, indent=2, ensure_ascii=False)}\n---\nSua tarefa é criar uma resposta final... Formate usando Markdown... contendo:\n1. Uma seção "Análise Detalhada".\n2. Uma seção "Recomendações de Segurança" em lista numerada.\n{fontes_prompt_section}"""
    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        if not response.parts: return f"A resposta do Agente Validador foi bloqueada. Razão: {response.prompt_feedback.block_reason.name}"
        return response.text
    except Exception as e:
        return "Ocorreu um erro ao gerar a resposta final."


# --- Funções de UI ---
def get_risk_color(risk_level: str) -> str:
    risk_level = risk_level.lower()
    if risk_level == "alto": return "#FF4B4B"
    if risk_level == "médio": return "#FFC700"
    if risk_level == "baixo": return "#28A745"
    return "#6c757d"

def display_analysis_results(analysis_data, full_response):
    risk_level = analysis_data.get("risco", "Indeterminado")
    risk_color = get_risk_color(risk_level)
    st.markdown(f"**Nível de Risco Identificado:** <span style='color:{risk_color}; font-weight: bold;'>{risk_level.upper()}</span>", unsafe_allow_html=True)
    with st.expander("Ver análise completa e recomendações", expanded=True):
        st.markdown(full_response)

# --- CSS Personalizado ---
def load_css():
    st.markdown("""<style>...</style>""", unsafe_allow_html=True) # Mantido o mesmo CSS

# --- Lógica Principal da Aplicação ---
def run_analysis(prompt_parts):
    if not prompt_parts:
        st.warning("Por favor, insira um texto ou envie uma imagem para análise.")
        return
    with st.spinner("Analisando com o Agente 1 (Flash)..."):
        st.session_state.analysis_data = call_analyzer_agent(prompt_parts)
    analysis_data = st.session_state.analysis_data
    if analysis_data and "error" not in analysis_data:
        with st.spinner("Validando análise com o Agente 2 (Flash)..."):
            st.session_state.full_response = call_validator_agent(analysis_data)
    else:
        error_message = f"Não foi possível obter uma análise. Razão: {analysis_data.get('error', 'Erro desconhecido') if analysis_data else 'Erro na análise inicial'}"
        st.error(error_message)
        st.session_state.full_response = None
        st.session_state.analysis_data = None

# --- Interface Principal ---
if 'text_for_analysis' not in st.session_state:
    st.session_state.text_for_analysis = ""

load_css()
sidebar_col, main_col = st.columns([28, 72])

with sidebar_col:
    st.markdown("""<div class="sidebar-content">...</div>""", unsafe_allow_html=True)

with main_col:
    st.markdown("<h3>Verificador de Conteúdo Suspeito</h3>", unsafe_allow_html=True)
    st.write("Insira texto, imagem ou grave um áudio para iniciar a análise.")

    text_input = st.text_area("Conteúdo textual:", value=st.session_state.text_for_analysis, height=150, key="text_area_input")
    st.session_state.text_for_analysis = text_input
    
    uploaded_image = st.file_uploader("Envie uma imagem (opcional):", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        st.image(uploaded_image, caption="Imagem a ser analisada", width=250)

    # --- ATUALIZAÇÃO: Componente de Gravação de Áudio Corrigido ---
    st.markdown("<h5>Grave um áudio (opcional):</h5>", unsafe_allow_html=True)
    
    webrtc_ctx = webrtc_streamer(
        key="audio_recorder",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        media_stream_constraints={"video": False, "audio": True},
        # CORREÇÃO: Passa a configuração RTC diretamente, sem ClientSettings
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )

    if not webrtc_ctx.state.playing:
        if st.session_state.get("audio_buffer"):
            if st.button("Transcrever Áudio Gravado"):
                audio_frames = list(st.session_state["audio_buffer"].values())
                if audio_frames:
                    sound_chunk = av.AudioFrame.link_frames(audio_frames)
                    
                    wav_buffer = io.BytesIO()
                    with av.open(wav_buffer, mode='w', format='wav') as container:
                        stream = container.add_stream('pcm_s16le', rate=48000)
                        for frame in sound_chunk.split():
                            container.mux(stream.encode(frame))
                    
                    wav_bytes = wav_buffer.getvalue()
                    
                    with st.spinner("Transcrevendo áudio..."):
                        transcript = transcribe_audio_to_text(wav_bytes, "recorded_audio.wav")
                        st.session_state.text_for_analysis = transcript
                        st.session_state["audio_buffer"] = {} # Limpa o buffer
                        st.rerun()
                else:
                    st.warning("Nenhum áudio foi gravado.")
    
    if webrtc_ctx.audio_receiver:
        try:
            for frame in webrtc_ctx.audio_receiver.get_frames(timeout=1):
                st.session_state["audio_buffer"][frame.time] = frame
        except Exception:
            pass
    
    # --- Fim do Componente de Gravação ---

    if st.button("Verificar Agora", key="submit_unified"):
        prompt_parts = []
        if st.session_state.text_for_analysis:
            prompt_parts.append(st.session_state.text_for_analysis)
        if uploaded_image:
            prompt_parts.append(Image.open(uploaded_image))
        run_analysis(prompt_parts)

    if 'analysis_data' in st.session_state and st.session_state.analysis_data and "error" not in st.session_state.analysis_data:
        display_analysis_results(st.session_state.analysis_data, st.session_state.full_response)
