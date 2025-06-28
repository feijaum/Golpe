import streamlit as st
import json

# --- Configuração da Página ---
# Usamos o layout "wide" para aproveitar melhor o espaço da tela, como no design.
st.set_page_config(
    page_title="Verificador de Golpes com IA",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Funções de Simulação dos Agentes de IA ---
# Estas funções simulam o comportamento dos agentes Gemini que definimos no plano.
# Elas nos permitem desenvolver a interface sem fazer chamadas reais à API.

def call_analyzer_agent(user_input: str) -> dict:
    """
    Simula o Agente 1 (Gemini 1.5 Flash).
    Recebe o input do usuário e retorna uma primeira análise em formato JSON.
    """
    print(f"ANALYZER: Analisando o input: '{user_input[:30]}...'")
    mock_response = {
        "analise": "O link parece ser uma tentativa de phishing clássica, usando um senso de urgência e um link encurtado para esconder o destino real. Foram encontrados relatos de golpes similares usando o nome da empresa 'Supt Scam'.",
        "risco": "Alto",
        "fontes": [
            "https.www.security.com/blog/phishing-report-2024",
            "https.forum.scam-detector.com/t/supt-scam-warning/12345"
        ]
    }
    return mock_response

def call_validator_agent(analysis_from_agent_1: dict) -> str:
    """
    Simula o Agente 2 (Gemini 1.5 Pro).
    Recebe a análise do primeiro agente e retorna o veredito final para o usuário.
    """
    print("VALIDATOR: Validando a análise recebida.")
    risco = analysis_from_agent_1.get("risco", "Indeterminado")
    fontes = analysis_from_agent_1.get("fontes", [])
    
    # Monta uma resposta final mais elaborada e amigável para o usuário
    # Usando Markdown para formatação
    veredito = f"""
    ### Veredito Final da Análise
    
    **Nível de Risco Identificado:** {risco}
    
    **Análise Detalhada:**
    A análise inicial indica uma forte possibilidade de golpe. O padrão identificado é consistente com táticas de **phishing**, onde criminosos tentam roubar suas informações pessoais (senhas, dados de cartão) se passando por uma empresa legítima.
    
    **Recomendações de Segurança:**
    1.  **NÃO CLIQUE** em nenhum link presente na mensagem.
    2.  **NÃO FORNEÇA** nenhuma informação pessoal ou financeira.
    3.  **BLOQUEIE** o remetente e **APAGUE** a mensagem imediatamente.
    4.  Se a mensagem se passar por uma empresa que você conhece, entre em contato com a empresa através de seus canais oficiais (site ou app) para verificar a legitimidade.
    
    **Fontes Consultadas pelo Analista:**
    """
    for fonte in fontes:
        veredito += f"- `{fonte}`\n"
        
    return veredito

# --- CSS e HTML Personalizado ---
def load_css():
    st.markdown("""
    <style>
        /* Remove o padding padrão do Streamlit para controle total */
        .block-container {
            padding: 1rem 2rem 2rem 2rem;
        }

        /* Oculta o menu de hambúrguer e o cabeçalho do Streamlit */
        #MainMenu, header {
            visibility: hidden;
        }

        /* Estilos para as colunas que agora formam nosso layout */
        /* Sidebar (Coluna da Esquerda) */
        .sidebar-content {
            background-color: #1e293b; /* Azul escuro do design */
            color: #ffffff;
            padding: 2rem;
            height: 85vh;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
        }
        .sidebar-content h1 {
            font-size: 2rem;
            font-weight: bold;
            display: flex;
            align-items: center;
        }
        .sidebar-content h2 {
            font-size: 1.5rem;
            margin-top: 2rem;
            color: #e2e8f0;
            line-height: 1.4;
        }
        .sidebar-content .call-to-action {
            margin-top: auto; /* Empurra o botão para o final */
            background-color: #4f46e5; /* Roxo/azul do botão */
            color: white;
            border: none;
            padding: 1rem;
            width: 100%;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .sidebar-content .call-to-action:hover {
            background-color: #4338ca;
        }

        /* Conteúdo Principal (Coluna da Direita) */
        .main-content {
            background-color: #f8fafc; /* Fundo cinza claro */
            padding: 2rem;
            height: 85vh;
            border-radius: 20px;
            overflow-y: auto;
        }
        
        /* Estilo para a área de resposta */
        .response-area {
            margin-top: 2rem;
            padding: 1.5rem;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            min-height: 250px;
        }
        
        /* Estilo para o botão de verificação */
        .stButton>button {
            background-color: #4f46e5;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: bold;
            border: none;
            width: auto;
            float: right; /* Alinha o botão à direita */
        }
    </style>
    """, unsafe_allow_html=True)

# --- Interface Principal do Aplicativo ---

load_css()

# Criação do layout principal com duas colunas
sidebar_col, main_col = st.columns([28, 72]) # Proporção 28%/72%

# --- Coluna da Esquerda (Sidebar) ---
with sidebar_col:
    st.markdown("""
    <div class="sidebar-content">
        <h1>🛡️ Verificador</h1>
        <h2>Análise Inteligente<br>de Golpes na Internet</h2>
        <button class="call-to-action">Aprenda a se Proteger</button>
    </div>
    """, unsafe_allow_html=True)

# --- Coluna da Direita (Conteúdo Principal) ---
with main_col:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    st.markdown("### Verificador de Conteúdo Suspeito")
    st.write("Cole um texto, mensagem ou link abaixo para iniciar a análise.")

    # Inputs do usuário
    user_input = st.text_area(
        "Conteúdo a ser analisado:", 
        height=150, 
        placeholder="Ex: Recebi um SMS dizendo que ganhei um prêmio, com o link bit.ly/premio123. É confiável?",
        label_visibility="collapsed"
    )

    submit_button = st.button("Verificar Agora")

    # Lógica para processar e exibir a resposta
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = ""

    if submit_button and user_input:
        with st.spinner("Analisando com o Agente 1 (Flash)..."):
            analysis = call_analyzer_agent(user_input)
        
        with st.spinner("Validando análise com o Agente 2 (Pro)..."):
            st.session_state.analysis_result = call_validator_agent(analysis)
    
    # Exibe o resultado se ele existir
    if st.session_state.analysis_result:
        st.markdown('<div class="response-area">', unsafe_allow_html=True)
        # CORREÇÃO: unsafe_allow_html=True para renderizar o Markdown corretamente
        st.markdown(st.session_state.analysis_result, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
