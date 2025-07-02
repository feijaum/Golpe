import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import io
# Importa a biblioteca de gravação de áudio
from streamlit_mic_recorder import mic_recorder
# ATUALIZAÇÃO: Importa a biblioteca para gerar PDF
from fpdf import FPDF, XPos, YPos
import re

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

def call_analyzer_agent(prompt_parts: list) -> dict:
    """
    Chama o Agente 1 (Gemini 1.5 Flash) para uma análise multimodal.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")

    full_prompt = [
        """
        Você é um especialista em cibersegurança (Agente Analisador). Analise o seguinte conteúdo fornecido por um usuário (pode ser texto, imagem, áudio ou uma combinação).
        Sua tarefa é retornar APENAS um objeto JSON. A estrutura deve ser:
        {
          "analise": "Uma análise técnica detalhada sobre os possíveis riscos, identificando padrões de phishing, malware, engenharia social, etc. Se houver áudio, baseie sua análise no conteúdo do áudio.",
          "risco": "Baixo", "Médio" ou "Alto",
          "fontes": ["url_da_fonte_1", "url_da_fonte_2"]
        }
        Baseie sua análise em pesquisas na internet para garantir que a informação seja atual. Se não encontrar fontes, retorne uma lista vazia.
        """
    ] + prompt_parts
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
    
    fontes_prompt_section = '### Fontes Consultadas pelo Analista' if analysis_from_agent_1.get("fontes", []) else ""
    prompt = f"""Você é um especialista em comunicação de cibersegurança. Um analista júnior forneceu o seguinte JSON:\n---\n{json.dumps(analysis_from_agent_1, indent=2, ensure_ascii=False)}\n---\nSua tarefa é criar uma resposta final para um usuário leigo. A resposta deve ser clara, direta e útil. NÃO use títulos como 'Veredito Final'. Comece diretamente com a análise. Formate sua resposta usando Markdown. A resposta DEVE conter as seguintes seções, usando exatamente estes títulos com '###':\n### Análise Detalhada\n### Recomendações de Segurança\n{fontes_prompt_section}"""
    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        if not response.parts: return f"A resposta do Agente Validador foi bloqueada."
        return response.text
    except Exception as e:
        return "Ocorreu um erro ao gerar a resposta final."

# --- FUNÇÃO DE GERAR PDF ATUALIZADA ---
def generate_pdf(risk_level, full_response):
    """Gera um PDF a partir dos resultados da análise."""
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 16)
    
    # Título
    pdf.cell(0, 10, "Relatorio de Analise de Risco", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    # Nível de Risco
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Nivel de Risco Identificado: {risk_level.upper()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Corpo do relatório
    pdf.set_font("Helvetica", "", 12)
    
    # Limpa o texto de markdown e codifica para latin-1 para o PDF
    cleaned_response = re.sub(r'###\s*|\*\*\s*|\*\s*', '', full_response)
    text_for_pdf = cleaned_response.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, text_for_pdf)
    
    # CORREÇÃO: pdf.output() retorna um bytearray, que deve ser convertido para bytes para o st.download_button
    return bytes(pdf.output())

# --- Funções de UI ---
def get_risk_color(risk_level: str) -> str:
    risk_level = risk_level.lower()
    if risk_level == "alto": return "#FF4B4B"
    if risk_level == "médio": return "#FFC700"
    if risk_level == "baixo": return "#28A745"
    return "#6c757d"

def display_analysis_results(analysis_data, full_response):
    """
    ATUALIZAÇÃO: Exibe os resultados de forma mais estruturada e visualmente agradável.
    """
    risk_level = analysis_data.get("risco", "Indeterminado")
    risk_color = get_risk_color(risk_level)
    
    st.markdown(f"**Nível de Risco Identificado:** <span style='color:{risk_color}; font-weight: bold;'>{risk_level.upper()}</span>", unsafe_allow_html=True)
    
    # Divide a resposta em seções usando os títulos ###
    sections = re.split(r'###\s*(.*?)\n', full_response)
    
    # Dicionário para guardar as seções
    parsed_sections = {}
    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        content = sections[i+1].strip()
        parsed_sections[title] = content

    # Exibe cada seção de forma estruturada
    if "Análise Detalhada" in parsed_sections:
        st.subheader("🔍 Análise Detalhada")
        st.markdown(parsed_sections["Análise Detalhada"])

    if "Recomendações de Segurança" in parsed_sections:
        st.subheader("🛡️ Recomendações de Segurança")
        recommendations = parsed_sections["Recomendações de Segurança"].split('\n')
        for rec in recommendations:
            # CORREÇÃO: Remove números e todos os asteriscos antes de exibir
            rec_text = re.sub(r'^\d+\.\s*|\*|\*\*', '', rec).strip()
            if rec_text:
                st.markdown(f"<div class='recommendation-card'>{rec_text}</div>", unsafe_allow_html=True)

    if "Fontes Consultadas pelo Analista" in parsed_sections:
        st.subheader("🔗 Fontes Consultadas")
        st.markdown(parsed_sections["Fontes Consultadas pelo Analista"])

    # Botão de download do PDF
    pdf_bytes = generate_pdf(risk_level, full_response)
    st.download_button(
        label="Salvar Relatório em PDF",
        data=pdf_bytes,
        file_name="relatorio_analise_risco.pdf",
        mime="application/pdf"
    )

# --- CSS Personalizado ---
def load_css():
    st.markdown("""
    <style>
        .block-container { padding: 1rem 2rem 2rem 2rem; }
        #MainMenu, header { visibility: hidden; }
        
        /* ATUALIZAÇÃO: Estilo da nova sidebar */
        .sidebar-content { 
            background-color: #ffffff; 
            border: 2px solid #4f46e5; /* Cor da borda igual à dos botões */
            color: #0F172A; /* Texto escuro para contraste */
            padding: 2rem; 
            height: 90vh; 
            border-radius: 20px; 
            display: flex; 
            flex-direction: column; 
        }
        .sidebar-content h1, .sidebar-content h2 { 
            color: #0F172A !important; /* Garante que o texto seja escuro */
        }
        .sidebar-content h2 { 
            font-size: 1.5rem; 
            margin-top: 2rem; 
            line-height: 1.4; 
        }
        /* ATUALIZAÇÃO: Estilo do botão/link "Aprenda a se Proteger" */
        .sidebar-content .call-to-action { 
            margin-top: auto; 
            background-color: #4f46e5; 
            color: white !important; /* Garante texto branco no botão */
            text-decoration: none;
            display: block;
            text-align: center;
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
            color: white !important;
        }

        [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div:nth-child(2) { background-color: #f8fafc; padding: 2rem; height: 90vh; border-radius: 20px; overflow-y: auto; }
        .stButton>button { background-color: #4f46e5; color: white; padding: 0.75rem 1.5rem; border-radius: 10px; font-size: 1rem; font-weight: bold; border: none; width: 100%; margin-top: 1rem; }
        p, li, h3, h2, h1 { color: #0F172A !important; }

        .recommendation-card {
            background-color: #ffffff;
            border-left: 5px solid #4f46e5;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* ATUALIZAÇÃO: Media Query para Responsividade */
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem;
            }
            /* Força colunas a empilhar */
            [data-testid="stHorizontalBlock"] {
                flex-direction: column;
            }
            /* Ajusta altura para auto em telas pequenas */
            .sidebar-content, [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div:nth-child(2) {
                height: auto;
                margin-bottom: 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# --- Lógica Principal da Aplicação ---
def run_analysis(prompt_parts):
    if not prompt_parts:
        st.warning("Por favor, insira um texto, imagem ou áudio para análise.")
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
sidebar_col, main_col = st.columns([30, 70]) # Ajuste de proporção

with sidebar_col:
    # ATUALIZAÇÃO: O botão agora é um link <a> com a mesma classe
    st.markdown("""<div class="sidebar-content">
        <h1>🛡️ Verificador</h1>
        <h2>Análise Inteligente<br>de Golpes na Internet</h2>
        <a href="#" target="_blank" class="call-to-action">Aprenda a se Proteger</a>
    </div>""", unsafe_allow_html=True)

with main_col:
    st.markdown("<h3>Verificador de Conteúdo Suspeito</h3>", unsafe_allow_html=True)
    st.write("Insira texto, imagem ou áudio para iniciar a análise.")

    # ATUALIZAÇÃO: Layout de input com duas colunas
    input_col, options_col = st.columns([60, 40])

    with input_col:
        text_input = st.text_area("Conteúdo textual:", height=300, key="text_area_input")
        # ATUALIZAÇÃO: Botão movido para baixo da caixa de texto
        verify_button = st.button("Verificar Agora", key="submit_unified")
    
    with options_col:
        uploaded_image = st.file_uploader("Envie uma imagem:", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(uploaded_image, caption="Imagem a ser analisada", use_column_width=True)
        
        st.markdown("---")
        
        uploaded_audio = st.file_uploader("Envie um ficheiro de áudio:", type=["wav", "mp3", "m4a", "ogg"])
        if uploaded_audio:
            st.audio(uploaded_audio)
            
        st.markdown("<h6>Ou grave um áudio:</h6>", unsafe_allow_html=True)
        audio_info = mic_recorder(
            start_prompt="Gravar",
            stop_prompt="Parar",
            key='recorder'
        )
        if audio_info and audio_info['bytes']:
            st.audio(audio_info['bytes'])
    
    # Lógica de verificação agora é chamada aqui, após todos os inputs serem definidos
    if verify_button:
        st.session_state.analysis_data = None
        st.session_state.full_response = None

        prompt_parts = []
        if text_input:
            prompt_parts.append(text_input)
        if uploaded_image:
            prompt_parts.append(Image.open(uploaded_image))
        
        audio_to_process = None
        if uploaded_audio:
            audio_to_process = uploaded_audio.getvalue()
        elif audio_info and audio_info['bytes']:
            audio_to_process = audio_info['bytes']

        if audio_to_process:
            audio_file = genai.upload_file(path=io.BytesIO(audio_to_process), mime_type="audio/wav")
            prompt_parts.append(audio_file)

        run_analysis(prompt_parts)

    results_placeholder = st.empty()
    with results_placeholder.container():
        if 'analysis_data' in st.session_state and st.session_state.analysis_data and "error" not in st.session_state.analysis_data:
            display_analysis_results(st.session_state.analysis_data, st.session_state.full_response)
