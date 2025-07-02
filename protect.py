import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Guia de Segurança Digital",
    page_icon="🛡️",
    layout="wide"
)

# --- CONFIGURAÇÃO DA API DO GEMINI ---
# Instrução para o usuário:
# 1. Crie um arquivo .streamlit/secrets.toml no diretório do seu app
# 2. Adicione sua chave da API nele:
#    GEMINI_API_KEY = "SUA_CHAVE_API_AQUI"
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except (KeyError, FileNotFoundError):
    st.error("A chave da API do Gemini não foi encontrada. Por favor, configure-a em .streamlit/secrets.toml")
    model = None


# --- ESTILOS CSS CUSTOMIZADOS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Criando um arquivo CSS temporário para injetar
with open("style.css", "w") as f:
    f.write("""
    .stApp {
        background-color: #F0F2F6;
    }
    .st-emotion-cache-1y4p8pa {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #1F2937;
    }
    .st-emotion-cache-16txtl3 {
        padding: 1.5rem;
        border-radius: 0.75rem;
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
    }
    .stButton>button {
        background-color: #4F46E5;
        color: white;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #4338CA;
        color: white;
    }
    """)

local_css("style.css")


# --- FUNÇÕES AUXILIARES ---
def gerar_senha(frase):
    """Gera uma senha forte a partir de uma frase."""
    if len(frase) < 10:
        return "Erro: Use uma frase mais longa para uma senha mais forte."
    
    password = ''
    words = frase.split(' ')
    for i, word in enumerate(words):
        if len(word) > 0:
            password += word[0].upper() if i % 2 == 0 else word[0].lower()
    
    password = password.replace('a', '@').replace('e', '3').replace('i', '!').replace('o', '0')
    numbers = ''.join(filter(str.isdigit, frase))
    password += f"_{numbers}" if numbers else "_25!"
    return password

def gerar_relato_golpe(tipo_golpe, prejuizo, descricao):
    """Chama a API do Gemini para gerar um texto de relato de golpe."""
    if not model:
        return "API do Gemini não configurada."

    prompt = f"""
    Aja como um assistente para uma vítima de golpe no Brasil. Com base nas informações a seguir, escreva um texto formal e claro, em português do Brasil, para ser usado em um boletim de ocorrência ou em um contato com o banco. Organize o texto com parágrafos claros.

    - **Tipo de Golpe:** {tipo_golpe}
    - **Prejuízo:** {prejuizo}
    - **Descrição dos Fatos:** {descricao}

    O texto deve ser objetivo, relatando os fatos de forma cronológica e precisa, para que a autoridade ou o gerente do banco possa entender claramente o que aconteceu. Comece com "Assunto: Relato de Ocorrência de Estelionato Virtual" e termine com um espaço para o nome e a data.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Erro ao gerar o relato: {e}")
        return "Não foi possível gerar o relato no momento."

# --- LAYOUT DA PÁGINA ---

st.title("🛡️ Seu Escudo Digital")
st.markdown("---")

# --- SEÇÃO 1: PANORAMA ---
with st.container(border=True):
    st.header("O Campo de Batalha Digital")
    st.write(
        "Vivemos em um mundo conectado, mas essa conveniência traz riscos. Os crimes virtuais no Brasil não são mais uma exceção. Esta seção mostra a dimensão do problema e explica a principal arma dos golpistas: a manipulação."
    )

    st.subheader("Crescimento Alarmante de Golpes no Brasil")
    st.write("O número de golpes e estelionatos digitais cresceu 360% em 7 anos.")

    # Gráfico com Altair
    chart_data = pd.DataFrame({
        'Ano': ['2017', '2024'],
        'Índice de Golpes': [100, 460],
        'Crescimento': ['Base', '+360%']
    })
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Ano:N', title='Ano'),
        y=alt.Y('Índice de Golpes:Q', title='Índice (Base 100)'),
        color=alt.Color('Ano:N', scale=alt.Scale(range=['#A5B4FC', '#4F46E5']), legend=None),
        tooltip=['Ano', 'Crescimento']
    ).properties(
        width='container',
        height=300
    )
    st.altair_chart(chart, use_container_width=True)

# --- SEÇÃO 2: ARMADILHAS ---
st.markdown("---")
with st.container(border=True):
    st.header("Conheça as Armadilhas")
    st.write(
        "Os criminosos são criativos, mas seus métodos costumam seguir padrões. Expanda cada tipo de golpe abaixo para entender como ele funciona, quais são os sinais de alerta e como se proteger."
    )
    
    golpes = {
        "🎣 Phishing e Smishing": "Golpistas enviam e-mails ou SMS falsos se passando por empresas famosas para 'pescar' seus dados. **Sinais de alerta:** senso de urgência, erros de português, links suspeitos.",
        "📱 Golpe do WhatsApp": "Criminosos clonam sua conta ou criam um perfil falso com sua foto para pedir dinheiro aos seus contatos. **Regra de Ouro:** Sempre ligue para a pessoa (em chamada normal) para confirmar qualquer pedido de dinheiro.",
        "🛒 Lojas e Ofertas Fantasma": "Sites falsos anunciam produtos por preços muito baixos para roubar seu dinheiro e seus dados. **Sinais de alerta:** preços bons demais para ser verdade, aceita apenas Pix para pessoa física.",
        "💰 Falsos Investimentos": "Um falso consultor promete lucros altíssimos, rápidos e sem risco. **Sinais de alerta:** promessas de lucro milagroso e pressão para decidir rápido.",
        "🤖 Golpes com IA": "Uso de IA para criar vídeos (deepfakes) ou clonar vozes para aplicar golpes de forma mais realista. **Defesa:** Crie uma 'palavra de segurança' com familiares para usar em emergências."
    }

    for titulo, descricao in golpes.items():
        with st.expander(titulo):
            st.write(descricao)

# --- SEÇÃO 3: PREVENÇÃO ---
st.markdown("---")
with st.container(border=True):
    st.header("Construa sua Fortaleza Digital")
    st.write("A segurança digital não exige conhecimento técnico avançado, mas sim a adoção de hábitos simples e eficazes.")

    st.subheader("1. Crie Senhas Fortes e Únicas")
    frase = st.text_input("Digite uma frase para gerar uma senha:", placeholder="Ex: Meu cachorro Bob nasceu em 2015!")
    if st.button("Gerar Senha"):
        senha_gerada = gerar_senha(frase)
        if "Erro" in senha_gerada:
            st.error(senha_gerada)
        else:
            st.success("Senha gerada com sucesso!")
            st.code(senha_gerada, language=None)

    st.subheader("2. Ative a Autenticação de Dois Fatores (2FA)")
    st.write("A 2FA é uma tranca extra. Mesmo que alguém roube sua senha, não conseguirá acessar sua conta sem um segundo código do seu celular. Ative em todas as suas contas importantes (WhatsApp, Instagram, e-mail, bancos).")

    st.subheader("3. Checklist do Comprador Seguro")
    st.checkbox("O site começa com **https://** e tem um cadeado? 🔒")
    st.checkbox("Os preços não são **bons demais para ser verdade**?")
    st.checkbox("O site tem informações claras como **CNPJ e endereço**?")
    st.checkbox("A reputação no **Reclame Aqui** é boa?")
    st.checkbox("A loja oferece **pagamentos seguros** como cartão de crédito?")


# --- SEÇÃO 4: SOCORRO ---
st.markdown("---")
with st.container(border=True):
    st.header("� Fui Vítima de um Golpe!")
    st.write("Descobrir um golpe é assustador, mas agir rápido pode fazer toda a diferença. Siga o plano de ação e use nosso assistente para ajudar a formalizar sua denúncia.")

    st.subheader("Plano de Ação Imediato")
    st.markdown("""
    - **Passo 1: Contate o Banco:** Ligue imediatamente para a central oficial do seu banco para bloquear cartões e contas.
    - **Passo 2: Altere Suas Senhas:** Mude a senha do seu e-mail principal primeiro, depois das outras contas.
    - **Passo 3: Faça um Boletim de Ocorrência (B.O.):** Registre um B.O. online na delegacia virtual do seu estado.
    - **Passo 4: Tente Recuperar o Dinheiro (MED do Pix):** Se o golpe foi via Pix, peça ao seu banco para acionar o Mecanismo Especial de Devolução.
    """)

    st.subheader("✨ Assistente para Relato de Golpe")
    st.write("Preencha os detalhes abaixo e nossa IA criará um texto formal para seu boletim de ocorrência ou para o contato com o banco.")

    tipo_golpe = st.text_input("Qual foi o tipo de golpe?", placeholder="Ex: Pix para loja falsa, WhatsApp clonado")
    prejuizo = st.text_input("O que você perdeu?", placeholder="Ex: R$ 500,00, acesso à conta do Instagram")
    descricao = st.text_area("Descreva brevemente como o golpe aconteceu:")

    if st.button("Gerar Relato"):
        if tipo_golpe and prejuizo and descricao:
            with st.spinner("Gerando relato com a IA..."):
                relato_gerado = gerar_relato_golpe(tipo_golpe, prejuizo, descricao)
                st.text_area("Relato Gerado:", value=relato_gerado, height=300)
                st.success("Relato gerado com sucesso! Copie o texto acima.")
        else:
            st.warning("Por favor, preencha todos os campos para gerar o relato.")
�
