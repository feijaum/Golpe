import streamlit as st
import json

# --- Configuração da Página ---
st.set_page_config(
    page_title="Verificador de Golpes com IA",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Funções de Simulação dos Agentes de IA ---
def call_analyzer_agent(user_input: str) -> dict:
    """
    Simula o Agente 1 (Gemini 1.5 Flash).
    Retorna uma análise em formato JSON.
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
    Recebe a análise e retorna o veredito final formatado como HTML.
    """
    print("VALIDATOR: Validando a análise recebida.")
    risco = analysis_from_agent_1.get("risco", "Indeterminado")
    analise_detalhada = analysis_from_agent_1.get("analise", "Nenhuma análise detalhada disponível.")
    fontes = analysis_from_agent_1.get("fontes", [])
    
    # Monta a resposta final em HTML para ter controle total sobre a renderização
    veredito_html = f"""
    <p><b>Nível de Risco Identificado:</b> {risco}</p>
    
    <p><b>Análise Detalhada:</b><br>
    {analise_detalhada} O padrão identificado é consistente com táticas de <b>phishing</b>, onde criminosos tentam roubar suas informações pessoais (senhas, dados de cartão) se passando por uma empresa legítima.</p>
    
    <p><b>Recomendações de Segurança:</b></p>
    <ol>
        <li><b>NÃO CLIQUE</b> em nenhum link presente na mensagem.</li>
        <li><b>NÃO FORNEÇA</b> nenhuma informação pessoal ou financeira.</li>
        <li><b>BLOQUEIE</b> o remetente e <b>APAGUE</b> a mensagem imediatamente.</li>
        <li>Se a mensagem se passar por uma empresa que você conhece, entre em contato com a empresa através de seus canais oficiais (site ou app) para verificar a legitimidade.</li>
    </ol>
    
    <p><b>Fontes Consultadas pelo Analista:</b></p>
    <ul>
    """
    for fonte in fontes:
        veredito_html += f"<li><code>{fonte}</code></li>"
    
    veredito_html += "</ul>"
    return veredito_html

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
            background-color: #1e293b;
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
            margin-top: auto;
            background-color: #4f46e5;
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
        /* Estiliza o container da coluna gerado pelo Streamlit */
        [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div:nth-child(2) {
             background-color: #f8fafc;
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
        .response-area p, .response-area li {
            color: #334155; /* Cor de texto mais escura para contraste */
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
            float: right;
            margin-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Interface Principal do Aplicativo ---

load_css()

# Criação do layout principal com duas colunas
sidebar_col, main_col = st.columns([28, 72])

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
    st.markdown("<h3>Verificador de Conteúdo Suspeito</h3>", unsafe_allow_html=True)
    st.write("Cole um texto, mensagem ou link abaixo para iniciar a análise.")

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
        # Injota o resultado HTML formatado dentro de uma div com a classe da área de resposta
        st.markdown(
            f'<div class="response-area">{st.session_state.analysis_result}</div>', 
            unsafe_allow_html=True
        )
