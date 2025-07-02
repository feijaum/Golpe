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
import base64
import pandas as pd
import altair as alt
# ATUALIZAÇÃO: Importa a biblioteca para o botão de copiar
import streamlit.components.v1 as components

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
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# --- FUNÇÕES DO AGENTE DE IA (VERIFICADOR) ---
def call_analyzer_agent(prompt_parts: list) -> dict:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    safety_settings = {'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE', 'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH', 'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
    full_prompt = ["""
        Você é um especialista em cibersegurança (Agente Analisador). Analise o seguinte conteúdo fornecido por um usuário (pode ser texto, imagem, áudio ou uma combinação).
        Sua tarefa é retornar APENAS um objeto JSON. A estrutura deve ser:
        {
          "analise": "Uma análise técnica detalhada sobre os possíveis riscos, identificando padrões de phishing, malware, engenharia social, etc. Se houver áudio, baseie sua análise no conteúdo do áudio.",
          "risco": "Baixo", "Médio" ou "Alto",
          "fontes": ["url_da_fonte_1", "url_da_fonte_2"]
        }
        Baseie sua análise em pesquisas na internet para garantir que a informação seja atual. Se não encontrar fontes, retorne uma lista vazia.
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
    prompt = f"""Você é um especialista em comunicação de cibersegurança. Um analista júnior forneceu o seguinte JSON:\n---\n{json.dumps(analysis, indent=2, ensure_ascii=False)}\n---\nSua tarefa é criar uma resposta final para um usuário leigo. A resposta deve ser clara, direta e útil. NÃO use títulos como 'Veredito Final'. Comece diretamente com a análise. Formate sua resposta usando Markdown. A resposta DEVE conter as seguintes seções, usando exatamente estes títulos com '###':\n### Análise Detalhada\n### Recomendações de Segurança\n{fontes_prompt_section}"""
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
    prompt = f"""Aja como um assistente para uma vítima de golpe no Brasil. Com base nas informações a seguir, escreva um texto formal e claro, em português do Brasil, para ser usado em um boletim de ocorrência ou em um contato com o banco. Organize o texto com parágrafos claros.\n\n- **Tipo de Golpe:** {tipo}\n- **Prejuízo:** {prejuizo}\n- **Descrição dos Fatos:** {descricao}\n\nO texto deve ser objetivo, relatando os fatos de forma cronológica e precisa, para que a autoridade ou o gerente do banco possa entender claramente o que aconteceu. Comece com "Assunto: Relato de Ocorrência de Estelionato Virtual" e termine com um espaço para o nome e a data."""
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
    with st.sidebar:
        qrcode_b64 = get_image_as_base64("qrcodepix.jpeg")
        qrcode_data_uri = f"data:image/jpeg;base64,{qrcode_b64}" if qrcode_b64 else "https://placehold.co/200x200/ffffff/000000?text=QR+Code+Nao+Encontrado"
        pix_key = "00020101021126580014br.gov.bcb.pix01369aa2c17a-3621-4f52-9872-71fb9d1cc6b25204000053039865802BR5925Antonio Batista Leite Bis6009SAO PAULO622905251JZ5NK7F1B11G1CWMRAY7RF8763042488"

        st.markdown(f"""
            <div class="sidebar-content">
                <h1><img src="{page_icon_data}" width=32> Verificador</h1>
                <h2>Análise Inteligente de Golpes na Internet</h2>
                <div class="donation-section">
                    <h4>Apoie este Projeto</h4>
                    <p>Este é um projeto gratuito. Se ele foi útil para você, considere fazer uma doação para ajudar a mantê-lo no ar.</p>
                    <img src="{qrcode_data_uri}" alt="QR Code PIX" width="150">
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        components.html(f"""
            <textarea id="pix-key" style="position: absolute; left: -9999px;">{pix_key}</textarea>
            <button class="pix-button" onclick="copyPix()">Pix Copia e Cola</button>
            <script>
            function copyPix() {{
                var copyText = document.getElementById("pix-key");
                copyText.select();
                document.execCommand("copy");
            }}
            </script>
        """, height=50)

        st.markdown("""
        <div class="social-links">
            <a href="https://www.instagram.com/prof.jvictor/" target="_blank">Instagram</a> | 
            <a href="https://linkedin.com/in/jvictorll/" target="_blank">LinkedIn</a>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão para mudar de página
        if st.button("Aprenda a se Proteger", key="to_protect", use_container_width=True):
            st.session_state.current_page = "protect"
            st.rerun()

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
    st.markdown("---")
    with st.container(border=True):
        st.header("O Campo de Batalha Digital")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            chart_data = pd.DataFrame({'Ano': ['2017', '2024'], 'Índice de Golpes': [100, 460]})
            chart = alt.Chart(chart_data).mark_bar().encode(x=alt.X('Ano:N'), y=alt.Y('Índice de Golpes:Q'), color=alt.Color('Ano:N', scale=alt.Scale(range=['#A5B4FC', '#4F46E5']), legend=None)).properties(height=250)
            st.altair_chart(chart, use_container_width=True)
        with col2:
            st.write("""
            **O número de golpes e estelionatos digitais cresceu 360% em 7 anos no Brasil.**
            Este gráfico ilustra o crescimento alarmante, usando 2017 como base (índice 100). 
            A principal arma dos golpistas é a **engenharia social**: a arte de manipular pessoas para que elas mesmas forneçam suas informações ou seu dinheiro. Eles criam um senso de urgência, medo ou oportunidade para fazer você agir sem pensar.
            """)

    with st.container(border=True):
        st.header("Conheça as Armadilhas")
        golpes = {
            "🎣 Phishing e Smishing": "O golpista envia e-mails (Phishing) ou SMS (Smishing) fingindo ser uma empresa conhecida (banco, loja, etc.). A mensagem geralmente contém um link que leva a um site falso, idêntico ao original, para roubar sua senha e dados. **Sinais de alerta:** senso de urgência ('sua conta será bloqueada'), erros de português e links que parecem estranhos.",
            "📱 Golpe do WhatsApp Clonado": "Criminosos conseguem o código de verificação do seu WhatsApp e ativam sua conta em outro aparelho. A partir daí, eles se passam por você para pedir dinheiro emprestado aos seus contatos. **Regra de Ouro:** Ative a 'Confirmação em duas etapas' nas configurações do WhatsApp e nunca compartilhe seu código de 6 dígitos.",
            "🛒 Lojas e Ofertas Fantasma": "Sites ou perfis em redes sociais anunciam produtos populares (celulares, eletrônicos) por preços muito abaixo do mercado. Após o pagamento (geralmente via Pix), o produto nunca é enviado e o site desaparece. **Sinais de alerta:** preços bons demais para ser verdade, site com aparência amadora e aceita apenas Pix ou boleto.",
            "💰 Falsos Investimentos e Pirâmides": "Um 'consultor' entra em contato prometendo lucros altíssimos, rápidos e sem risco, geralmente com criptomoedas ou ações. No início, eles podem até pagar pequenos valores para ganhar sua confiança, mas o objetivo é fazer você investir uma grande quantia que nunca mais verá. **Sinais de alerta:** promessas de lucro garantido e pressão para decidir rápido.",
            "🤖 Golpes com IA (Deepfake)": "A tecnologia de Inteligência Artificial é usada para criar vídeos ou áudios falsos (deepfakes) de pessoas conhecidas. Um golpista pode usar um áudio clonado da sua voz para ligar para um familiar e pedir dinheiro numa emergência. **Defesa:** Crie uma 'palavra de segurança' com familiares e amigos próximos para confirmar a identidade em situações suspeitas."
        }
        for titulo, descricao in golpes.items():
            with st.expander(titulo): st.write(descricao)
            
    # ... (Restante do conteúdo da página de proteção) ...

def load_css():
    st.markdown("""
    <style>
        #MainMenu, header { visibility: hidden; }
        
        /* ATUALIZAÇÃO: Estilo da nova sidebar branca com borda */
        [data-testid="stSidebar"] > div:first-child {
            background-color: #ffffff;
            border-right: 2px solid #4f46e5;
        }
        
        .sidebar-content h1, .sidebar-content h2, .sidebar-content h4, .sidebar-content p { 
            color: #0F172A !important; 
        }
        .donation-section {
            margin-top: 2rem;
            text-align: center;
        }
        .social-links {
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 2rem;
        }
        .social-links a {
            text-decoration: none;
            color: #4f46e5;
            margin: 0 10px;
        }

        /* Estilo do botão PIX */
        .pix-button { 
            background-color: #4f46e5; 
            color: white !important; 
            padding: 0.5rem 1rem;
            border-radius: 10px; 
            font-weight: bold; 
            border: none;
            width: 100%;
            cursor: pointer;
            margin-top: 1rem;
        }
        .pix-button:hover {
            background-color: #4338ca;
        }

        .stButton>button { 
            background-color: #4f46e5; 
            color: white; 
            border-radius: 10px; 
            font-weight: bold; 
            border: none;
        }
        .stButton>button:hover {
            background-color: #4338ca;
        }
        
        button[kind="secondary"] {
            background-color: transparent !important;
            color: #4f46e5 !important;
            border: 1px solid #4f46e5 !important;
        }
        
        .main-content-area, .stApp {
             background-color: #f8fafc;
        }

        p, li, h3, h2, h1 { color: #0F172A !important; }

        .recommendation-card {
            background-color: #ffffff;
            border-left: 5px solid #4f46e5;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

# --- PONTO DE ENTRADA PRINCIPAL ---
load_css()
if st.session_state.current_page == "verifier":
    show_verifier_page()
else:
    show_protect_page()
