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

# --- ESTADO DA SESSÃO ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "verifier"
if 'text_for_analysis' not in st.session_state:
    st.session_state.text_for_analysis = ""

# --- FUNÇÕES DO AGENTE DE IA (VERIFICADOR) ---
def call_analyzer_agent(prompt_parts: list) -> dict:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
    full_prompt = ["Você é um especialista em cibersegurança..."] + prompt_parts # Prompt omitido para brevidade
    try:
        response = model.generate_content(full_prompt, generation_config=generation_config, safety_settings=safety_settings)
        if not response.parts: return {"error": "A resposta foi bloqueada."}
        return json.loads(response.text)
    except Exception as e:
        return {"error": "Erro ao contactar a IA.", "details": str(e)}

def call_validator_agent(analysis: dict) -> str:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    prompt = f"Você é um especialista em comunicação... JSON recebido:\n{json.dumps(analysis, indent=2, ensure_ascii=False)}\nCrie uma resposta final..." # Prompt omitido para brevidade
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
    prompt = f"Aja como um assistente... Tipo: {tipo}, Prejuízo: {prejuizo}, Descrição: {descricao}..." # Prompt omitido para brevidade
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
    st.markdown(f"**Nível de Risco:** <span style='color:{get_risk_color(risk)};'>{risk.upper()}</span>", unsafe_allow_html=True)
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
    load_css()
    sidebar_col, main_col = st.columns([30, 70])
    with sidebar_col:
        st.markdown(f"""<div class="sidebar-content">
            <h1><img src="{page_icon_data}" width=32> Verificador</h1>
            <h2>Análise Inteligente de Golpes na Internet</h2>
            </div>""", unsafe_allow_html=True)
        # Botão para mudar de página
        if st.button("Aprenda a se Proteger", key="to_protect"):
            st.session_state.current_page = "protect"
            st.rerun()

    with main_col:
        st.markdown("<h3>Verificador de Conteúdo Suspeito</h3>", unsafe_allow_html=True)
        input_col, options_col = st.columns([60, 40])
        with input_col:
            text_input = st.text_area("Conteúdo textual:", height=300)
            verify_button = st.button("Verificar Agora")
        with options_col:
            uploaded_image = st.file_uploader("Envie uma imagem:", type=["jpg", "png"])
            uploaded_audio = st.file_uploader("Envie um áudio:", type=["wav", "mp3", "m4a"])
            audio_info = mic_recorder("Gravar", "Parar", key='recorder')
        
        if verify_button:
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
                        st.session_state.analysis_results = None
        
        if "analysis_results" in st.session_state and st.session_state.analysis_results:
            display_analysis_results(*st.session_state.analysis_results)

def show_protect_page():
    load_css(protect_page=True)
    if st.button("⬅️ Voltar ao Verificador"):
        st.session_state.current_page = "verifier"
        st.rerun()
    st.title("🛡️ Seu Escudo Digital")
    # ... (Todo o conteúdo da UI de protect.py vai aqui) ...
    with st.container(border=True):
        st.header("O Campo de Batalha Digital")
        # ... (Gráfico e texto) ...
    with st.container(border=True):
        st.header("Conheça as Armadilhas")
        # ... (Expanders de golpes) ...
    with st.container(border=True):
        st.header("Construa sua Fortaleza Digital")
        # ... (Gerador de senha e checklist) ...
    with st.container(border=True):
        st.header("🆘 Fui Vítima de um Golpe!")
        # ... (Assistente de relato) ...

def load_css(protect_page=False):
    # CSS principal
    main_css = """...""" # Omitido para brevidade
    # CSS específico da página de proteção
    protect_css = """...""" # Omitido para brevidade
    st.markdown(f"<style>{main_css}{protect_css if protect_page else ''}</style>", unsafe_allow_html=True)

# --- PONTO DE ENTRADA PRINCIPAL ---
if st.session_state.current_page == "verifier":
    show_verifier_page()
else:
    show_protect_page()
