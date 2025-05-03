# Know Your Fan - Desafio #2 [HARD] 🚀

Aplicação Web desenvolvida como parte do Challenge #2 (Know Your Fan) do processo seletivo para Assistente de Engenharia de Software.

## Descrição

Este projeto simula uma solução de "Know Your Fan" (KYF), uma estratégia usada por organizações para conhecer melhor seus fãs. O objetivo é demonstrar a coleta, armazenamento e uma análise **simulada** de informações sobre um fã de e-sports (usando os dados do próprio desenvolvedor como exemplo).

A aplicação foi construída em Flask (Python) e permite ao usuário:

- Cadastrar e editar informações básicas de perfil e interesses em e-sports.
- Realizar o upload de uma imagem placeholder para simular o envio de documentos.
- Executar uma validação simulada por "IA" no documento placeholder usando OCR (Tesseract).
- Adicionar links para perfis em sites de e-sports (HLTV, Liquipedia, etc.).
- Executar uma validação simulada por "IA" nesses links, verificando a presença de palavras-chave relevantes.
- Adicionar links para perfis em redes sociais.
- Exibir todas as informações coletadas e os resultados das validações simuladas em uma página de perfil.

**Nota Importante sobre Privacidade e Simulação:** Devido às implicações da LGPD e à complexidade técnica, funcionalidades que envolvem dados altamente sensíveis (CPF, validação real de identidade) ou integrações complexas (OAuth, análise profunda de redes sociais) foram **simplificadas ou simuladas** para focar nos conceitos de integração e fluxo de dados, conforme detalhado na seção "Simulações e Limitações".

## Funcionalidades Implementadas

- **Gerenciamento de Perfil:** Criação e edição de perfil de fã com campos para nome, email (opcional), localização (cidade/estado), times favoritos, jogos favoritos, interesses gerais e atividades/compras relacionadas a e-sports no último ano.
- **Upload de Documento (Placeholder):** Campo para upload de arquivos de imagem (JPG/PNG). O arquivo é salvo localmente.
- **Validação de Documento (Simulada com OCR):** Utiliza Tesseract OCR via `pytesseract` para tentar extrair texto da imagem placeholder enviada. O resultado (texto extraído ou mensagem de erro/status) é exibido. **Não realiza validação de identidade real.**
- **Links de Perfis E-sports:** Campo para inserir múltiplos links (um por linha) para perfis em sites como HLTV, Liquipedia, etc.
- **Validação de Links (Simulada com Keywords):** Tenta acessar cada URL fornecida, baixa o HTML (se não for bloqueado), extrai o texto e verifica a presença de palavras-chave relacionadas aos times e jogos favoritos do usuário. Exibe um status como "Relevante", "Não Relevante" ou "Não verificado (Erro)".
- **Links de Redes Sociais:** Campos para inserir URLs de perfis em redes sociais (Twitter, Twitch, Facebook, Instagram, TikTok).
- **Análise Social (Simulada):** Exibe uma mensagem estática indicando que uma análise foi realizada (sem integração real com APIs sociais ou NLP).
- **Visualização do Perfil:** Página que exibe todos os dados coletados e os resultados das validações simuladas.
- **Banco de Dados:** Utiliza SQLite para armazenamento persistente dos dados do perfil.

## Tecnologias Utilizadas

- **Linguagem:** Python 3
- **Framework Web:** Flask
- **Banco de Dados:** SQLite
- **ORM:** Flask-SQLAlchemy (wrapper para SQLAlchemy)
- **Formulários Web:** Flask-WTF (wrapper para WTForms)
- **Requisições HTTP (Validação Links):** `httpx` (assíncrono)
- **Parsing HTML (Validação Links):** `BeautifulSoup4`
- **OCR (Validação Documento):** `pytesseract` (wrapper para Tesseract OCR)
- **Manipulação de Imagem (OCR):** `Pillow`
- **Variáveis de Ambiente:** `python-dotenv`
- **Gerenciador de Ambiente:** `pipenv`
- **Dependência Externa:** Tesseract OCR Engine (precisa ser instalado no sistema operacional)

## Configuração e Instalação

**Pré-requisitos:**

- Python 3.11.4
- `pipenv` instalado (`pip install pipenv`)
- **Tesseract OCR Engine instalado:** Baixe e instale a partir de [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki). **Importante:** Durante a instalação, inclua o pacote de idioma Português (`por`).

**Passos:**

1.  **Clone o Repositório:**

    ```bash
    git clone [https://github.com/lilkirito22/know-your-fan-app.git](https://github.com/lilkirito22/know-your-fan-app.git)
    cd [know-your-fan-app]
    ```

2.  **Instale as Dependências Python:**

    ```bash
    pipenv install
    ```

3.  **Configure as Variáveis de Ambiente:**

    - Crie um arquivo chamado `.env` na raiz do projeto.
    - Use o arquivo `.env.example` (que você deve criar) como modelo.
    - Preencha os valores no `.env`:
      - `SECRET_KEY`: Gere uma chave forte e aleatória (ex: `python -c 'import secrets; print(secrets.token_hex(24))'`).
      - `SQLALCHEMY_DATABASE_URI`: Define onde o arquivo do banco de dados SQLite será criado. O padrão `sqlite:///fan_profiles.db` o criará na raiz do projeto.

    **Estrutura do `.env.example`:**

    ```dotenv
    # Chave secreta para segurança do Flask (sessões, CSRF)
    SECRET_KEY='gere_uma_chave_secreta_forte_e_aleatoria_aqui'

    # URI do Banco de Dados SQLite (cria 'fan_profiles.db' na raiz do projeto)
    SQLALCHEMY_DATABASE_URI='sqlite:///fan_profiles.db'

    # Desativa recurso não utilizado do SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    ```

4.  **Configure o Caminho do Tesseract (se necessário):**
    - Se o Tesseract não foi adicionado ao PATH do sistema durante a instalação, localize onde o `tesseract.exe` foi instalado (geralmente `C:\Program Files\Tesseract-OCR\`).
    - No arquivo `app.py`, encontre a seção comentada `# --- <<< POTENCIALMENTE NECESSÁRIO: Configurar Caminho do Tesseract >>> ---`.
    - Descomente a linha `pytesseract.pytesseract.tesseract_cmd = r'...'` e coloque o caminho **completo** para o seu `tesseract.exe` dentro do `r''`.

## Executando o App

1.  **Ative o Ambiente Virtual (opcional):**
    ```bash
    pipenv shell
    ```
2.  **Inicie o Servidor Flask:**
    ```bash
    python app.py
    ```
    (Ou `pipenv run python app.py` se não ativou o shell).
3.  **Acesse no Navegador:** Abra seu navegador e vá para `http://127.0.0.1:5000` (ou o endereço indicado no terminal). Você será redirecionado para a página `/edit` para criar seu perfil.

## Simulações, Limitações e Melhorias Futuras

Este projeto utiliza simulações para cumprir alguns requisitos complexos de IA e evitar problemas de privacidade, focando na demonstração da arquitetura e integração:

- **Dados Sensíveis:** **Não coleta CPF ou documentos de identidade reais**, em respeito à LGPD e segurança. O upload de documento aceita apenas imagens placeholder.
- **Validação de Documento:** A validação por "IA" é **simulada** usando Tesseract OCR para _tentar_ extrair texto da imagem placeholder. **Não realiza verificação de identidade real.** A funcionalidade depende da correta instalação e configuração do Tesseract OCR e seus pacotes de idioma no sistema.
- **Vinculação/Análise Social:** Apenas URLs de perfis sociais são armazenadas (input manual). A "análise" é **simulada** com um texto estático. A integração real via OAuth e APIs sociais não foi implementada devido à complexidade.
- **Validação de Links E-sports:** Utiliza uma abordagem básica de **web scraping e busca por palavras-chave**. Essa validação é **limitada** e pode falhar:
  - Sites como HLTV podem **bloquear** requisições automáticas (resultando em Erro 403).
  - A busca por keywords pode não encontrar termos relevantes em páginas de login ou com estrutura complexa (resultando em "Não Relevante").
- **Melhorias Futuras:** Integrar APIs sociais reais (OAuth), usar serviços de IA mais avançados (Cloud Vision, Natural Language API) para validações e análises menos simuladas, implementar paginação para listas longas, adicionar mais funcionalidades (ranking, resultados H2H, etc.), usar um banco de dados mais robusto (PostgreSQL) e implementar Migrations (Flask-Migrate).

## Autor

[Daniel Chaves Castro]

- GitHub: [Link para seu GitHub: https://github.com/lilkirito22]
- LinkedIn: [https://www.linkedin.com/in/daniel-chaves-castro/]
