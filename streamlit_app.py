import streamlit as st
import google.generativeai as genai
import json

# --- Configuração da Página e API ---
st.set_page_config(
    page_title="Verificador de Golpes com IA",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configura a API do Gemini usando a chave guardada nos segredos do Streamlit
try:
    genai.configure(api_key=st.secrets["google_api"]["key"])
except Exception as e:
    st.error(f"Erro ao configurar a API do Google. Verifique se a seção [google_api] e a chave 'key' estão corretas no secrets.toml. Erro: {e}")
    st.stop()


# --- Funções dos Agentes de IA (COM MAIS ROBUSTEZ) ---

def call_analyzer_agent(user_input: str) -> dict:
    """
    Chama o Agente 1 (Gemini 1.5 Flash) para uma análise inicial.
    Agora inclui configuração de segurança e força a saída para ser JSON.
    """
    # ATUALIZAÇÃO: Modelo agora especifica que a resposta deve ser JSON
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    # ATUALIZAÇÃO: Configuração explícita dos filtros de segurança.
    # Isto é importante para uma aplicação que precisa de analisar conteúdo potencialmente nocivo.
    safety_settings = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }

    # ATUALIZAÇÃO: Usar response_mime_type para forçar a saída em JSON.
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")

    prompt = f"""
    Você é um especialista em cibersegurança (Agente Analisador). Analise o seguinte conteúdo fornecido por um usuário:
    ---
    {user_input}
    ---
    Sua tarefa é retornar APENAS um objeto JSON.
    A estrutura deve ser:
    {{
      "analise": "Uma análise técnica detalhada sobre os possíveis riscos, identificando padrões de phishing, malware, engenharia social, etc.",
      "risco": "Baixo", "Médio" ou "Alto",
      "fontes": ["url_da_fonte_1", "url_da_fonte_2"]
    }}
    Baseie sua análise em pesquisas na internet para garantir que a informação seja atual.
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        # Verifica se a resposta foi bloqueada
        if not response.parts:
             return {"error": "A resposta foi bloqueada.", "details": f"Razão do bloqueio: {response.prompt_feedback.block_reason.name}"}

        json_response = json.loads(response.text)
        return json_response
    except Exception as e:
        print(f"Erro na chamada do Agente Analisador: {e}")
        return {"error": "Ocorreu um erro inesperado ao contactar a IA.", "details": str(e)}


def call_validator_agent(analysis_from_agent_1: dict) -> str:
    """
    Chama o Agente 2 (Gemini 1.5 Pro) para validar e formatar a resposta final.
    """
    if "error" in analysis_from_agent_1:
        return f"Ocorreu um erro na análise inicial. Detalhes: {analysis_from_agent_1.get('details', '')}"

    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    Você é um especialista em comunicação de cibersegurança (Agente Validador). Um analista júnior forneceu o seguinte JSON com uma análise de risco:
    ---
    {json.dumps(analysis_from_agent_1, indent=2, ensure_ascii=False)}
    ---
    Sua tarefa é criar uma resposta final para um usuário leigo. A resposta deve ser clara, direta e útil.
    NÃO use títulos como 'Veredito Final'. Comece diretamente com a análise.
    Formate sua resposta usando Markdown.
    A resposta deve conter:
    1.  Uma seção "Análise Detalhada".
    2.  Uma seção "Recomendações de Segurança" em formato de lista numerada.
    3.  Uma seção "Fontes Consultadas pelo Analista" com as URLs.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro no Agente Validador: {e}")
        return "Ocorreu um erro ao gerar a resposta final."


# --- Funções de UI ---

def get_risk_color(risk_level: str) -> str:
    """Retorna uma cor baseada no nível de risco."""
    risk_level = risk_level.lower()
    if risk_level == "alto":
        return "#FF4B4B"  # Vermelho
    elif risk_level == "médio":
        return "#FFC700"  # Amarelo
    elif risk_level == "baixo":
        return "#28A745"  # Verde
    return "#6c757d"  # Cinza para indeterminado

def display_analysis_results(analysis_data, full_response):
    """Exibe os resultados da análise de forma estruturada."""
    
    risk_level = analysis_data.get("risco", "Indeterminado")
    risk_color = get_risk_color(risk_level)
    
    st.markdown(f"**Nível de Risco Identificado:** <span style='color:{risk_color}; font-weight: bold;'>{risk_level.upper()}</span>", unsafe_allow_html=True)

    with st.expander("Ver análise completa e recomendações", expanded=True):
        st.markdown(full_response)


# --- CSS Personalizado ---
def load_css():
    st.markdown("""
    <style>
        .block-container { padding: 1rem 2rem 2rem 2rem; }
        #MainMenu, header { visibility: hidden; }

        .sidebar-content {
            background-color: #1e293b; color: #ffffff; padding: 2rem;
            height: 85vh; border-radius: 20px; display: flex; flex-direction: column;
        }
        .sidebar-content h1 { font-size: 2rem; font-weight: bold; }
        .sidebar-content h2 { font-size: 1.5rem; margin-top: 2rem; color: #e2e8f0; line-height: 1.4; }
        .sidebar-content .call-to-action {
            margin-top: auto; background-color: #4f46e5; color: white; border: none;
            padding: 1rem; width: 100%; border-radius: 10px; font-size: 1rem;
            font-weight: bold; cursor: pointer; transition: background-color 0.3s;
        }
        .sidebar-content .call-to-action:hover { background-color: #4338ca; }
        
        [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div:nth-child(2) {
             background-color: #f8fafc; padding: 2rem; height: 85vh;
             border-radius: 20px; overflow-y: auto;
        }
        
        .stExpander {
            border: 1px solid #e2e8f0 !important;
            border-radius: 15px !important;
            background-color: #ffffff;
        }
        .stExpander [data-testid="stExpanderDetails"] {
            padding-top: 1rem;
        }
        
        .stButton>button {
            background-color: #4f46e5; color: white; padding: 0.75rem 1.5rem;
            border-radius: 10px; font-size: 1rem; font-weight: bold;
            border: none; width: auto; float: right; margin-top: 1rem;
        }
        p, li, h3 {
           color: #0F172A !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Interface Principal do Aplicativo ---

load_css()
sidebar_col, main_col = st.columns([28, 72])

with sidebar_col:
    st.markdown("""
    <div class="sidebar-content">
        <h1>🛡️ Verificador</h1>
        <h2>Análise Inteligente<br>de Golpes na Internet</h2>
        <button class="call-to-action">Aprenda a se Proteger</button>
    </div>
    """, unsafe_allow_html=True)

with main_col:
    st.markdown("<h3>Verificador de Conteúdo Suspeito</h3>", unsafe_allow_html=True)
    st.write("Cole um texto, mensagem ou link abaixo para iniciar a análise.")

    user_input = st.text_area(
        "Conteúdo a ser analisado:", height=150,
        placeholder="Ex: Recebi um SMS dizendo que ganhei um prêmio, com o link bit.ly/premio123. É confiável?",
        label_visibility="collapsed"
    )

    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'full_response' not in st.session_state:
        st.session_state.full_response = None

    if st.button("Verificar Agora") and user_input:
        with st.spinner("Analisando com o Agente 1 (Flash)..."):
            st.session_state.analysis_data = call_analyzer_agent(user_input)
        
        analysis_data = st.session_state.analysis_data
        if analysis_data and "error" not in analysis_data:
            with st.spinner("Validando análise com o Agente 2 (Pro)..."):
                st.session_state.full_response = call_validator_agent(analysis_data)
        else:
            # ATUALIZAÇÃO: Mostra o erro detalhado para o usuário
            error_details = analysis_data.get('details', 'Nenhum detalhe adicional.')
            error_message = f"Não foi possível obter uma análise. Razão: {analysis_data.get('error', 'Erro desconhecido')}"
            st.error(error_message)
            st.session_state.full_response = None # Limpa a resposta anterior
            st.session_state.analysis_data = None


    if st.session_state.analysis_data and st.session_state.full_response and "error" not in st.session_state.analysis_data:
        display_analysis_results(st.session_state.analysis_data, st.session_state.full_response)
