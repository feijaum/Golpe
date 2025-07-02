# 🛡️ Verificador de Golpes com IA

**Um assistente de cibersegurança multimodal que utiliza a API do Google Gemini para analisar textos, imagens e áudios, identificando potenciais golpes e fornecendo orientações de segurança para o utilizador.**

![Status](https://img.shields.io/badge/status-ativo-success.svg)
![Versão](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Licença](https://img.shields.io/badge/license-MIT-green.svg)

---

<!-- Adicione aqui um GIF de demonstração da sua aplicação -->
<!-- <p align="center">
  <img src="URL_DO_SEU_GIF_AQUI" alt="Demonstração do Verificador de Golpes" width="800"/>
</p> -->

## 📜 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [✨ Funcionalidades Principais](#-funcionalidades-principais)
- [🛠️ Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [🚀 Como Executar o Projeto](#-como-executar-o-projeto)
- [📁 Estrutura do Projeto](#-estrutura-do-projeto)
- [🤝 Como Contribuir](#-como-contribuir)
- [📄 Licença](#-licença)
- [📬 Contato e Apoio](#-contato-e-apoio)

---

## 📖 Sobre o Projeto

O **Verificador de Golpes com IA** nasceu da necessidade de criar uma ferramenta acessível e poderosa para proteger utilizadores comuns contra o número crescente de fraudes digitais no Brasil. A aplicação funciona como um chatbot onde qualquer pessoa, independentemente do seu conhecimento técnico, pode submeter um conteúdo suspeito (uma mensagem de texto, um print de uma conversa, um link ou um áudio) e receber uma análise de risco detalhada.

A arquitetura de IA utiliza um sistema de **dois agentes do Google Gemini**:
1.  **Agente Analisador:** Recebe o conteúdo, realiza uma pesquisa na internet em tempo real e faz uma primeira avaliação técnica.
2.  **Agente Validador:** Revisa a análise do primeiro agente, verifica a fiabilidade das fontes e traduz a informação técnica para uma resposta clara, objetiva e acionável para o utilizador final.

Além da verificação, o projeto inclui um **Guia de Segurança Digital** interativo, que educa o utilizador sobre os principais tipos de golpes e oferece ferramentas práticas, como um gerador de senhas e um assistente para a criação de relatos para boletins de ocorrência.

---

## ✨ Funcionalidades Principais

- **🔍 Análise Multimodal:** Capaz de processar e analisar **texto, imagens e áudio** (gravado ou enviado).
- **🤖 Arquitetura de IA com Dois Agentes:** Garante uma análise mais robusta e fiável, reduzindo a chance de erros.
- **🛡️ Guia de Segurança Interativo:** Educa os utilizadores sobre os tipos de golpes mais comuns e como se proteger.
- **📄 Geração de Relatórios em PDF:** Permite que o utilizador guarde um relatório completo da análise para referência futura.
- **🌗 Tema Claro e Escuro:** A interface adapta-se automaticamente ao tema do sistema operativo do utilizador, com a opção de troca manual.
- **📱 Interface Responsiva:** O design adapta-se a diferentes tamanhos de ecrã, de computadores a telemóveis.

---

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído com as seguintes tecnologias:

- **Linguagem:** Python
- **Framework Web:** Streamlit
- **Inteligência Artificial:** Google Gemini API (gemini-1.5-flash)
- **Visualização de Dados:** Pandas & Altair
- **Geração de PDF:** FPDF2
- **Interação com Áudio:** Streamlit-Mic-Recorder
- **Interação com o Navegador:** Streamlit-JS-Eval

---

## 🚀 Como Executar o Projeto

Para executar este projeto localmente, siga os passos abaixo:

1.  **Clone o Repositório**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

2.  **Crie um Ambiente Virtual** (Recomendado)
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
    ```

3.  **Instale as Dependências**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure a Chave da API**
    - Crie uma pasta chamada `.streamlit` na raiz do projeto.
    - Dentro dela, crie um ficheiro chamado `secrets.toml`.
    - Adicione sua chave da API do Google Gemini ao ficheiro da seguinte forma:
      ```toml
      [google_api]
      key = "SUA_CHAVE_API_AQUI"
      ```

5.  **Execute a Aplicação**
    ```bash
    streamlit run streamlit_app.py
    ```

---

## 📁 Estrutura do Projeto


.
├── .streamlit/
│   └── secrets.toml    # Ficheiro para as chaves de API (não versionado)
├── icon.svg            # Ícone da aplicação
├── qrcodepix.jpeg      # Imagem do QR Code para doações
├── requirements.txt    # Lista de dependências Python
├── streamlit_app.py    # Código principal da aplicação
└── README.md           # Este ficheiro


---

## 🤝 Como Contribuir

Contribuições são o que tornam a comunidade de código aberto um lugar incrível para aprender, inspirar e criar. Qualquer contribuição que você fizer será **muito apreciada**.

1.  Faça um "Fork" do projeto
2.  Crie uma "Branch" para sua funcionalidade (`git checkout -b feature/AmazingFeature`)
3.  Faça o "Commit" de suas alterações (`git commit -m 'Add some AmazingFeature'`)
4.  Faça o "Push" para a "Branch" (`git push origin feature/AmazingFeature`)
5.  Abra um "Pull Request"

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o ficheiro `LICENSE` para mais detalhes.

---

## 📬 Contato e Apoio

**J. Victor**

- **LinkedIn:** [linkedin.com/in/jvictorll](https://linkedin.com/in/jvictorll/)
- **Instagram:** [@prof.jvictor](https://www.instagram.com/prof.jvictor/)

Este é um projeto de uso livre e gratuito. Se ele foi útil para você, considere apoiar o seu desenvolvimento com uma doação. Qualquer valor é bem-vindo!

<!-- QR Code e Botão PIX -->
<p align="center">
  <img src="qrcodepix.jpeg" alt="QR Code PIX" width="200"/>
  <br>
  <strong>Chave PIX (Copia e Cola):</strong> <code>000201...2488</code>
</p>
