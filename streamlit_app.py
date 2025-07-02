import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import io
from streamlit_mic_recorder import mic_recorder
from fpdf import FPDF, XPos, YPos
import re
import base64
import pandas as pd
import altair as alt
import streamlit.components.v1 as components
# ATUALIZAÇÃO: Importa a biblioteca para executar JavaScript
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURAÇÃO DA PÁGINA E API ---
def get_image_as_base64(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

icon_b64 = get_image_as_base64("icon.svg")
page_icon_data = f"data:image/svg+xml;base64,{icon_b64}" if icon_b64 else "🛡️"

st.set_page_config(
    page_title="Verificador de Golpes com IA",
    page_icon=page_icon_data,
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    if "google_api" in st.secrets and "key" in st.secrets["google_api"]:
        genai.configure(api_key=st.secrets["google_api"]["key"])
    else:
        st.error("A configuração da chave de API do Google não foi encontrada.")
        st.stop()
except Exception as e:
    st.error(f"Ocorreu um erro ao configurar a API do Google: {e}")
    st.stop()

# --- ESTADO DA SESSÃO E ROTEAMENTO ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "verifier"
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'theme' not in st.session_state:
    st.session_state.theme = "Automático" # Valor inicial

# --- FUNÇÕES DO AGENTE DE IA (VERIFICADOR) ---
def call_analyzer_agent(prompt_parts: list) -> dict:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
    full_prompt = ["""
        Você é um especialista em cibersegurança (Agente Analisador)...
        """] + prompt_parts
    try:
        response = model.generate_content(full_prompt, generation_config=generation_config, safety_settings=safety_settings)
        if not response.parts: return {"error": "A resposta foi bloqueada."}
        return json.loads(response.text)
    except Exception as e:
        return {"error": "Erro ao contactar a IA.", "details": str(e)}

def call_validator_agent(analysis: dict) -> str:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    fontes_prompt_section = '### Fontes Consultadas' if analysis.get("fontes", []) else ""
    prompt = f"""Você é um especialista em comunicação de cibersegurança..."""
    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        if not response.parts: return "A resposta do Validador foi bloqueada."
        return response.text
    except Exception as e:
        return "Erro ao gerar a resposta final."

# --- FUNÇÕES DO GUIA DE SEGURANÇA (PROTECT) ---
def gerar_senha(frase):
    if len(frase) < 10: return "Erro: Use uma frase mais longa."
    password = ''.join([word[0].upper() if i % 2 == 0 else word[0].lower() for i, word in enumerate(frase.split()) if word])
    password = password.replace('a', '@').replace('e', '3').replace('i', '!').replace('o', '0')
    numbers = ''.join(filter(str.isdigit, frase))
    return f"{password}_{numbers}" if numbers else f"{password}_25!"

def gerar_relato_golpe(tipo, prejuizo, descricao):
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""Aja como um assistente para uma vítima de golpe no Brasil..."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao gerar o relato: {e}"

# --- FUNÇÕES DE UI ---
def get_risk_color(risk): return {"alto": "#FF4B4B", "médio": "#FFC700", "baixo": "#28A745"}.get(risk.lower(), "#6c757d")

def generate_pdf(risk, response):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Relatorio de Analise de Risco", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Nivel de Risco: {risk.upper()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 12)
    cleaned = re.sub(r'###\s*|\*\*|\*', '', response).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, cleaned)
    return bytes(pdf.output())

def display_analysis_results(data, response):
    risk = data.get("risco", "Indeterminado")
    st.markdown(f"**Nível de Risco:** <span style='color:{get_risk_color(risk)}; font-weight: bold;'>{risk.upper()}</span>", unsafe_allow_html=True)
    sections = {s[0].strip(): s[1].strip() for s in re.findall(r'###\s*(.*?)\n(.*?)(?=###|$)', response, re.S)}
    
    if "Análise Detalhada" in sections:
        st.subheader("🔍 Análise Detalhada")
        st.markdown(sections["Análise Detalhada"])
    if "Recomendações de Segurança" in sections:
        st.subheader("🛡️ Recomendações de Segurança")
        for rec in sections["Recomendações de Segurança"].split('\n'):
            rec_text = re.sub(r'^\d+\.\s*|\*|\*\*', '', rec).strip()
            if rec_text: st.markdown(f"<div class='recommendation-card'>{rec_text}</div>", unsafe_allow_html=True)
    if "Fontes Consultadas" in sections:
        st.subheader("🔗 Fontes Consultadas")
        st.markdown(sections["Fontes Consultadas"])
        
    pdf_bytes = generate_pdf(risk, response)
    st.download_button("Salvar Relatório em PDF", pdf_bytes, "relatorio.pdf", "application/pdf")

# --- LÓGICA DE RENDERIZAÇÃO DAS PÁGINAS ---

def show_verifier_page():
    st.markdown("<h3>Verificador de Conteúdo Suspeito</h3>", unsafe_allow_html=True)
    input_col, options_col = st.columns([60, 40])
    with input_col:
        text_input = st.text_area("Conteúdo textual:", height=300)
        verify_button = st.button("Verificar Agora", use_container_width=True)
    with options_col:
        uploaded_image = st.file_uploader("Envie uma imagem:", type=["jpg", "png"])
        uploaded_audio = st.file_uploader("Envie um áudio:", type=["wav", "mp3", "m4a"])
        audio_info = mic_recorder("Gravar", "Parar", key='recorder')
    
    if verify_button:
        st.session_state.analysis_results = None
        prompt_parts = []
        if text_input: prompt_parts.append(text_input)
        if uploaded_image: prompt_parts.append(Image.open(uploaded_image))
        audio_bytes = uploaded_audio.getvalue() if uploaded_audio else (audio_info['bytes'] if audio_info else None)
        if audio_bytes: prompt_parts.append(genai.upload_file(path=io.BytesIO(audio_bytes), mime_type="audio/wav"))
        
        if not prompt_parts:
            st.warning("Insira conteúdo para análise.")
        else:
            with st.spinner("Analisando..."):
                analysis_data = call_analyzer_agent(prompt_parts)
                if analysis_data and "error" not in analysis_data:
                    full_response = call_validator_agent(analysis_data)
                    st.session_state.analysis_results = (analysis_data, full_response)
                else:
                    st.error("Não foi possível obter uma análise.")
    
    if st.session_state.analysis_results:
        display_analysis_results(*st.session_state.analysis_results)

def show_protect_page():
    if st.button("⬅️ Voltar ao Verificador"):
        st.session_state.current_page = "verifier"
        st.rerun()
    st.title("🛡️ Seu Escudo Digital")
    # ... (Conteúdo da página de proteção)

def load_css():
    st.markdown("""
    <style>
        :root {
            --primary-bg: #f8fafc;
            --secondary-bg: #ffffff;
            --sidebar-bg: #ffffff;
            --sidebar-border: #4f46e5;
            --text-color: #0F172A;
            --sidebar-text-color: #0F172A;
            --button-bg: #4f46e5;
            --button-hover-bg: #4338ca;
            --button-text-color: #ffffff;
        }

        body.dark-theme {
            --primary-bg: #0F172A;
            --secondary-bg: #1e293b;
            --sidebar-bg: #1e293b;
            --sidebar-border: #a5b4fc;
            --text-color: #e2e8f0;
            --sidebar-text-color: #e2e8f0;
            --button-bg: #a5b4fc;
            --button-hover-bg: #818cf8;
            --button-text-color: #1e293b;
        }

        #MainMenu, header, button[data-testid="stSidebarNav-collapse-control"] { 
            display: none;
        }
        
        .stApp {
            background-color: var(--primary-bg);
        }
        
        [data-testid="stSidebar"] > div:first-child {
            background-color: var(--sidebar-bg);
            border-right: 2px solid var(--sidebar-border);
        }
        
        .sidebar-content h1, .sidebar-content h2, .sidebar-content h4, .sidebar-content p { 
            color: var(--sidebar-text-color) !important; 
        }
        
        .stButton>button { 
            background-color: var(--button-bg); 
            color: var(--button-text-color) !important;
        }
        .stButton>button:hover {
            background-color: var(--button-hover-bg);
        }
        
        .pix-button { color: var(--button-text-color) !important; }
        
        p, li, h3, h2, h1 { color: var(--text-color) !important; }

        .recommendation-card { 
            background-color: var(--secondary-bg); 
            border-left: 5px solid var(--button-bg);
        }
        
        /* Outros estilos omitidos para brevidade, mas devem usar variáveis */
    </style>
    """, unsafe_allow_html=True)

# --- PONTO DE ENTRADA PRINCIPAL ---
load_css()

# Lógica para aplicar o tema
is_dark_system = streamlit_js_eval(js_expressions="window.matchMedia('(prefers-color-scheme: dark)').matches", key="theme_detect")

theme_choice = st.session_state.theme
active_theme = "dark" if (theme_choice == "Escuro" or (theme_choice == "Automático" and is_dark_system)) else "light"

streamlit_js_eval(js_expressions=f"document.body.classList.remove('dark-theme', 'light-theme'); document.body.classList.add('{active_theme}-theme');", key="theme_apply")

# Renderiza a sidebar
with st.sidebar:
    st.radio(
        "Tema",
        ["Automático", "Claro", "Escuro"],
        key="theme",
        horizontal=True,
    )
    
    qrcode_b64 = get_image_as_base64("qrcodepix.jpeg")
    qrcode_data_uri = f"data:image/jpeg;base64,{qrcode_b64}" if qrcode_b64 else ""
    pix_key = "00020101021126580014br.gov.bcb.pix01369aa2c17a-3621-4f52-9872-71fb9d1cc6b25204000053039865802BR5925Antonio Batista Leite Bis6009SAO PAULO622905251JZ5NK7F1B11G1CWMRAY7RF8763042488"
    
    st.markdown(f'<div class="sidebar-content"><h1><img src="{page_icon_data}" width=32> Verificador</h1><h2>Análise Inteligente de Golpes na Internet</h2>', unsafe_allow_html=True)
    
    with st.expander("Apoie este Projeto"):
        st.markdown(f'<div class="donation-section"><p>Este projeto é gratuito...</p><img src="{qrcode_data_uri}" alt="QR Code PIX" width="150"></div>', unsafe_allow_html=True)
        components.html(f"""<textarea id="pix-key" style="position:absolute;left:-9999px;">{pix_key}</textarea><button class="pix-button" onclick="copyPix()">Pix Copia e Cola</button><script>function copyPix(){{var c=document.getElementById("pix-key");c.select();document.execCommand("copy");}}</script>""", height=50)

    st.markdown('<div class="social-links"><a href="https://www.instagram.com/prof.jvictor/" target="_blank">Instagram</a> | <a href="https://linkedin.com/in/jvictorll/" target="_blank">LinkedIn</a></div>', unsafe_allow_html=True)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    if st.session_state.current_page == "verifier":
        if st.button("Guia de Segurança", key="to_protect", use_container_width=True):
            st.session_state.current_page = "protect"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Renderiza a página principal
if st.session_state.current_page == "verifier":
    show_verifier_page()
else:
    show_protect_page()
