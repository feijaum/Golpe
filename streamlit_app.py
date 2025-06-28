import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
# ATUALIZAÇÃO: Importa a nova biblioteca de gravação de áudio
from st_audiorec import audio_recorder

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

# --- Estado da Sessão ---
if 'text_for_analysis' not in st.session_state:
    st.session_state.text_for_analysis = ""

# --- Funções dos Agentes de IA ---

def transcribe_audio_to_text(audio_bytes: bytes) -> str:
    """
    Envia bytes de áudio para o Gemini e retorna a transcrição.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = "Transcreva o seguinte áudio para texto. Retorne apenas o texto transcrito, sem nenhum outro comentário."
    
    try:
        # O Gemini pode processar os bytes de áudio WAV diretamente
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

    full_prompt = ["Você é um especialista em cibersegurança (Agente Analisador)..."] + prompt_parts
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
    if "error" in analysis_from_agent_1: return f"Ocorreu um erro na análise inicial."
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    prompt = f"""Você é um especialista em comunicação de cibersegurança..."""
    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        if not response.parts: return f"A resposta do Agente Validador foi bloqueada."
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
        st.error("Não foi possível obter uma análise.")
        st.session_state.full_response = None
        st.session_state.analysis_data = None

# --- Interface Principal ---
load_css()
sidebar_col, main_col = st.columns([28, 72])

with sidebar_col:
    st.markdown("""<div class="sidebar-content">...</div>""", unsafe_allow_html=True)

with main_col:
    st.markdown("<h3>Verificador de Conteúdo Suspeito</h3>", unsafe_allow_html=True)
    st.write("Insira texto, imagem ou grave um áudio para iniciar a análise.")

    # --- ATUALIZAÇÃO: Componente de Gravação de Áudio com st_audiorec ---
    audio_bytes = audio_recorder(
        text="Clique para Gravar",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_name="microphone",
        icon_size="2x",
    )
    
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        if st.button("Transcrever Áudio Gravado"):
            with st.spinner("Transcrevendo áudio..."):
                transcript = transcribe_audio_to_text(audio_bytes)
                st.session_state.text_for_analysis = transcript
                st.rerun()

    text_input = st.text_area("Conteúdo textual:", value=st.session_state.text_for_analysis, height=150, key="text_area_input")
    st.session_state.text_for_analysis = text_input
    
    uploaded_image = st.file_uploader("Envie uma imagem (opcional):", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        st.image(uploaded_image, caption="Imagem a ser analisada", width=250)
    
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
