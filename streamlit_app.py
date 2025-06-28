import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import io

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


# --- Funções dos Agentes de IA ---

def call_analyzer_agent(prompt_parts: list) -> dict:
    """
    Chama o Agente 1 (Gemini 1.5 Flash) para uma análise multimodal.
    Aceita uma lista de "partes" que podem ser texto ou imagens.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    safety_settings = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }

    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")

    # O prompt textual é adicionado como a primeira parte
    full_prompt = [
        """
        Você é um especialista em cibersegurança (Agente Analisador). Analise o seguinte conteúdo fornecido por um usuário (pode ser texto, imagem ou ambos).
        Sua tarefa é retornar APENAS um objeto JSON. A estrutura deve ser:
        {
          "analise": "Uma análise técnica detalhada sobre os possíveis riscos, identificando padrões de phishing, malware, engenharia social, etc.",
          "risco": "Baixo", "Médio" ou "Alto",
          "fontes": ["url_da_fonte_1", "url_da_fonte_2"]
        }
        Baseie sua análise em pesquisas na internet para garantir que a informação seja atual.
        """
    ] + prompt_parts

    try:
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        if not response.parts:
             return {"error": "A resposta foi bloqueada.", "details": f"Razão do bloqueio: {response.prompt_feedback.block_reason.name}"}

        json_response = json.loads(response.text)
        return json_response
    except Exception as e:
        print(f"Erro na chamada do Agente Analisador: {e}")
        return {"error": "Ocorreu um erro inesperado ao contactar a IA.", "details": str(e)}


def call_validator_agent(analysis_from_agent_1: dict) -> str:
    """
    Chama o Agente 2 (Gemini 1.5 Flash) para validar e formatar a resposta final.
    """
    if "error" in analysis_from_agent_1:
        return f"Ocorreu um erro na análise inicial. Detalhes: {analysis_from_agent_1.get('details', '')}"

    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    safety_settings = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }
    
    # ATUALIZAÇÃO: Lógica para incluir a seção de fontes apenas se existirem
    fontes = analysis_from_agent_1.get("fontes", [])
    fontes_prompt_section = ""
    if fontes:
        fontes_prompt_section = '3. Uma seção "Fontes Consultadas pelo Analista" com as URLs.'


    prompt = f"""
    Você é um especialista em comunicação de cibersegurança (Agente Validador). Um analista júnior forneceu o seguinte JSON:
    ---
    {json.dumps(analysis_from_agent_1, indent=2, ensure_ascii=False)}
    ---
    Sua tarefa é criar uma resposta final para um usuário leigo. A resposta deve ser clara, direta e útil.
    NÃO use títulos como 'Veredito Final'. Comece diretamente com a análise.
    Formate sua resposta usando Markdown. A resposta deve conter:
    1. Uma seção "Análise Detalhada".
    2. Uma seção "Recomendações de Segurança" em formato de lista numerada.
    {fontes_prompt_section}
    """
    try:
        response = model.generate_content(
            prompt,
            safety_settings=safety_settings
        )
        if not response.parts:
             return f"A resposta do Agente Validador foi bloqueada. Razão: {response.prompt_feedback.block_reason.name}"
        return response.text
    except Exception as e:
        print(f"Erro no Agente Validador: {e}")
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
    st.markdown("""<style>...</style>""", unsafe_allow_html=True) # O CSS foi omitido para brevidade, mas é o mesmo da versão anterior

# --- Lógica Principal da Aplicação ---
def run_analysis(prompt_parts):
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
load_css()
sidebar_col, main_col = st.columns([28, 72])

with sidebar_col:
    st.markdown("""<div class="sidebar-content">...</div>""", unsafe_allow_html=True) # HTML da sidebar omitido para brevidade

with main_col:
    st.markdown("<h3>Verificador de Conteúdo Suspeito</h3>", unsafe_allow_html=True)
    
    # ATUALIZAÇÃO: Interface com separadores para diferentes tipos de input
    tab_texto, tab_imagem, tab_audio = st.tabs(["Analisar Texto", "Analisar Imagem", "Analisar Áudio (em breve)"])

    # Separador de Texto
    with tab_texto:
        st.write("Cole um texto, mensagem ou link abaixo para iniciar a análise.")
        text_input = st.text_area("Conteúdo textual:", height=150, placeholder="Ex: Recebi um SMS...", label_visibility="collapsed")
        if st.button("Verificar Texto", key="submit_text"):
            if text_input:
                run_analysis([text_input])

    # Separador de Imagem
    with tab_imagem:
        st.write("Envie uma imagem (print de conversa, anúncio, etc.) para análise.")
        uploaded_image = st.file_uploader("Escolha uma imagem", type=["jpg", "jpeg", "png"])
        image_text_prompt = st.text_input("Adicione um contexto ou pergunta sobre a imagem (opcional):", placeholder="Ex: Esta mensagem que recebi é um golpe?")
        
        if uploaded_image is not None:
            st.image(uploaded_image, width=300)
            if st.button("Verificar Imagem", key="submit_image"):
                image = Image.open(uploaded_image)
                prompt_parts = [image_text_prompt, image]
                run_analysis(prompt_parts)

    # Separador de Áudio (Funcionalidade futura)
    with tab_audio:
        st.info("Em breve: A funcionalidade de análise de áudio está em desenvolvimento.")
        st.write("Você poderá gravar ou enviar um áudio para que a IA analise o conteúdo em busca de táticas de golpe por voz.")


    # Exibe os resultados
    if 'analysis_data' in st.session_state and st.session_state.analysis_data and "error" not in st.session_state.analysis_data:
        display_analysis_results(st.session_state.analysis_data, st.session_state.full_response)
