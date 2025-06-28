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
    # Apenas para garantir que a função está sendo chamada
    print(f"ANALYZER: Analisando o input: '{user_input[:30]}...'")
    
    # Resposta simulada em formato JSON, como esperado da API
    mock_response = {
        "analise": "O link parece ser uma tentativa de phishing clássica, usando um senso de urgência e um link encurtado para esconder o destino real. Foram encontrados relatos de golpes similares usando o nome da empresa 'Supt Scam'.",
        "risco": "Alto",
        "fontes": [
            "https://www.security.com/blog/phishing-report-2024",
            "https://forum.scam-detector.com/t/supt-scam-warning/12345"
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
    veredito = f"""
    ### Veredito Final da Análise
    
    **Nível de Risco Identificado: {risco}**
    
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
# Aqui injetamos o estilo (CSS) para replicar o design da imagem de referência.
# Usamos classes para estruturar o layout (sidebar, main-content) e estilizar os elementos.
def load_css():
    st.markdown("""
    <style>
        /* Remove o padding padrão do Streamlit para controle total */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Oculta o menu de hambúrguer e o cabeçalho do Streamlit */
        #MainMenu, header {
            visibility: hidden;
        }

        /* Container principal para o layout de duas colunas */
        .app-container {
            display: flex;
            height: 80vh; /* Altura da viewport */
            width: 100%;
            background-color: #ffffff;
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            overflow: hidden;
        }

        /* Sidebar (Coluna da Esquerda) */
        .sidebar {
            width: 25%;
            background-color: #1e293b; /* Azul escuro do design */
            color: #ffffff;
            padding: 2rem;
            display: flex;
            flex-direction: column;
        }
        .sidebar h1 {
            font-size: 2rem;
            font-weight: bold;
            display: flex;
            align-items: center;
        }
        .sidebar h2 {
            font-size: 1.5rem;
            margin-top: 2rem;
            color: #e2e8f0;
        }
         .sidebar .call-to-action {
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
        .sidebar .call-to-action:hover {
            background-color: #4338ca;
        }

        /* Conteúdo Principal (Coluna da Direita) */
        .main-content {
            width: 75%;
            padding: 2rem;
            background-color: #f8fafc; /* Fundo cinza claro */
            overflow-y: auto; /* Permite scroll se o conteúdo for grande */
        }
        
        /* Estilo para a área de resposta */
        .response-area {
            margin-top: 2rem;
            padding: 1.5rem;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            min-height: 300px;
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
            width: 100%;
        }

    </style>
    """, unsafe_allow_html=True)

# --- Interface Principal do Aplicativo ---

load_css()

# Usamos st.empty() para criar containers que podemos preencher com o nosso HTML
app_container = st.empty()

with app_container.container():
    st.markdown("""
    <div class="app-container">
        <div class="sidebar">
            <h1>🛡️ Verificador</h1>
            <h2>Análise Inteligente<br>de Golpes na Internet</h2>
            <!-- Placeholder para outros elementos da sidebar -->
            <button class="call-to-action">Aprenda a se Proteger</button>
        </div>
        
        <div class="main-content" id="main-content-area">
            <!-- O conteúdo do Streamlit irá aqui -->
        </div>
    </div>
    """, unsafe_allow_html=True)

# Agora, inserimos os componentes do Streamlit dentro da div 'main-content'
# Isso é um truque, pois o Streamlit não permite aninhar componentes diretamente em HTML.
# A abordagem correta é criar o layout com HTML e preencher as áreas com colunas do Streamlit.
# Para este MVP, vamos colocar os controles diretamente abaixo do layout HTML.

st.markdown("### Verificador de Conteúdo Suspeito")
st.write("Cole um texto, mensagem ou link abaixo para iniciar a análise.")

# Inputs do usuário
user_input = st.text_area(
    "Conteúdo a ser analisado:", 
    height=150, 
    placeholder="Ex: Recebi um SMS dizendo que ganhei um prêmio, com o link bit.ly/premio123. É confiável?"
)

submit_button = st.button("Verificar Agora")

# Container para a resposta
response_container = st.container()

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if submit_button and user_input:
    with st.spinner("Analisando com o Agente 1 (Flash)..."):
        analysis = call_analyzer_agent(user_input)
    
    with st.spinner("Validando análise com o Agente 2 (Pro)..."):
        st.session_state.analysis_result = call_validator_agent(analysis)

# Exibe o resultado se ele existir no estado da sessão
if st.session_state.analysis_result:
    with response_container:
        st.markdown('<div class="response-area">', unsafe_allow_html=True)
        st.markdown(st.session_state.analysis_result, unsafe_allow_html=False)
        st.markdown('</div>', unsafe_allow_html=True)


