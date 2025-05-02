# app.py
import os
import logging
import pytesseract # <<< Importa pytesseract
from PIL import Image # <<< Importa Pillow (Image)
from werkzeug.utils import secure_filename # <<< Importa para nomes de arquivo seguros
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List

# Carrega variáveis do .env
load_dotenv()

# Configuração do Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Configuração do App Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-default-secret-key-CHANGE-ME')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///fan_profiles.db') # Usando DB na raiz
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS','False').lower() == 'true'

# <<< NOVA CONFIGURAÇÃO: Pasta de Upload >>>
UPLOAD_FOLDER = 'uploads' # Nome da pasta onde os arquivos serão salvos
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER) # Cria a pasta se não existir
        logger.info(f"Pasta de uploads criada em: {os.path.abspath(UPLOAD_FOLDER)}")
    except OSError as e:
         logger.error(f"ERRO CRÍTICO: Falha ao criar pasta de uploads '{UPLOAD_FOLDER}': {e}")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicializa extensões
from models import db
db.init_app(app)
csrf = CSRFProtect(app)

# Importa modelos e formulários
from models import FanProfile
from forms import ProfileForm

# --- <<< POTENCIALMENTE NECESSÁRIO: Configurar Caminho do Tesseract >>> ---
# Se pyTesseract não achar o Tesseract sozinho, descomente e ajuste esta linha:
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # <<< AJUSTE ESTE CAMINHO PARA O SEU!!!
try:
    # Verifica se o caminho customizado existe antes de definir
    if os.path.exists(TESSERACT_PATH):
         pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
         tesseract_version = pytesseract.get_tesseract_version()
         logger.info(f"Tesseract OCR configurado manualmente para: {TESSERACT_PATH} (Versão: {tesseract_version})")
    else:
         # Tenta usar sem caminho (pode funcionar se estiver no PATH)
         tesseract_version = pytesseract.get_tesseract_version()
         logger.info(f"Tesseract OCR encontrado automaticamente no PATH (Versão: {tesseract_version}).")
except Exception as e:
    logger.error(f"Tesseract OCR NÃO encontrado automaticamente ou erro ao verificar versão. Configure o caminho manualmente se o OCR falhar. Erro: {e}")
    # Define como None se não encontrar, para checar depois
    pytesseract.pytesseract.tesseract_cmd = None


# Cria as tabelas no banco de dados
with app.app_context():
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    logger.info(f"Verificando/Criando banco de dados em: {db_uri}")
    try:
        db.create_all()
        logger.info("Tabelas do banco de dados verificadas/criadas com sucesso.")
    except Exception as e:
        logger.exception(f"ERRO CRÍTICO ao verificar/criar tabelas para URI '{db_uri}'")

# --- Rotas (Páginas) da Aplicação ---
async def validate_esports_link(url: str, keywords: List[str]) -> str:
    """
    Tenta buscar o conteúdo de uma URL e verifica se contém keywords.
    Retorna um status de validação simulada.
    """
    if not url.startswith(('http://', 'https://')):
        return "Inválido (URL mal formatada)"

    # Cabeçalho para simular um navegador comum e evitar bloqueios simples
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    status = "Não verificado (Erro)" # Status padrão

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            logger.info(f"Validando link: {url}")
            response = await client.get(url, headers=headers)
            response.raise_for_status() # Verifica se houve erro HTTP (4xx, 5xx)

            # Verifica tipo de conteúdo (só processamos HTML)
            content_type = response.headers.get('content-type', '').lower()
            if 'html' not in content_type:
                logger.warning(f"Link {url} não é HTML ({content_type}). Pulando validação de keyword.")
                return f"Não verificado (Não é HTML)"

            # Parseia o HTML e extrai texto
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text(" ", strip=True).lower() # Pega todo texto visível e converte para minúsculas

            # Verifica keywords
            found_keyword = False
            for keyword in keywords:
                if keyword in page_text:
                    logger.info(f"Keyword '{keyword}' encontrada em {url}")
                    found_keyword = True
                    break # Para na primeira keyword encontrada

            status = "Relevante (Keyword encontrada)" if found_keyword else "Não Relevante (Keyword não encontrada)"

    except httpx.TimeoutException:
        logger.warning(f"Timeout ao buscar link: {url}")
        status = "Não verificado (Timeout)"
    except httpx.RequestError as e:
        logger.warning(f"Erro de requisição ao buscar link {url}: {e}")
        status = f"Não verificado (Erro Conexão)"
    except httpx.HTTPStatusError as e:
         logger.warning(f"Erro HTTP {e.response.status_code} ao buscar link {url}")
         status = f"Não verificado (Erro {e.response.status_code})"
    except Exception as e:
        logger.error(f"Erro inesperado ao validar link {url}: {e}", exc_info=True)
        status = f"Não verificado (Erro inesperado)"

    logger.info(f"Resultado validação para {url}: {status}")
    return status



@app.route('/')
def view_profile():
    """Exibe o perfil do fã (ID=1)."""
    profile = None
    try:
        profile = db.session.get(FanProfile, 1)
        if not profile:
             logger.info("Perfil ID=1 não encontrado no DB ao carregar a view.")
             flash('Nenhum perfil encontrado (ID=1). Crie um!', 'info')
             return redirect(url_for('edit_profile'))
        logger.info(f"Renderizando profile.html para {profile.name}")
        return render_template('profile.html', profile=profile) # <<< CORRIGIDO return aqui
    except Exception as e:
        logger.exception(f"Erro ao buscar perfil ID=1 no DB para view")
        flash("Erro ao acessar o banco de dados.", "danger")
        # Em caso de erro aqui, talvez renderizar um template de erro?
        # Por simplicidade, redirecionamos para edição.
        return redirect(url_for('edit_profile'))


@app.route('/edit', methods=['GET', 'POST'])
async def edit_profile(): # <<< Tornar a rota async para usar await com asyncio.gather >>>
    """Exibe o formulário para criar/editar o perfil (ID=1) e processa."""
    profile = db.session.get(FanProfile, 1)
    form = ProfileForm(obj=profile)

    if form.validate_on_submit():
        was_new = False
        if profile is None:
            profile = FanProfile(id=1)
            db.session.add(profile)
            was_new = True
            logger.info("Objeto FanProfile novo criado (ID=1).")

        # Popula dados do formulário (exceto arquivo, que já é tratado)
        # Salva os links *antes* de popular, para termos acesso ao valor bruto
        raw_links_text = form.esports_profile_links.data
        profile.esports_profile_links = raw_links_text # Salva os links brutos

        form.populate_obj(profile) # Popula outros campos
        logger.info(f"Objeto FanProfile populado com dados do form.")

        # Lógica de Upload e OCR (como estava antes)
        file = form.document.data
        # ... (código do upload e OCR aqui) ...
        if file:
             # ... (salvar arquivo, rodar OCR, salvar resultados em profile...) ...
             pass # Mantenha seu código de OCR aqui


        # --- <<< NOVA LÓGICA: Validar Links E-sports >>> ---
        validation_results_text = "Nenhum link fornecido ou erro na validação."
        if raw_links_text:
            # Prepara keywords a partir dos interesses do usuário
            keywords_base = []
            if profile.favorite_teams:
                keywords_base.extend([team.strip().lower() for team in profile.favorite_teams.split(',') if team.strip()])
            if profile.favorite_games:
                 keywords_base.extend([game.strip().lower() for game in profile.favorite_games.split(',') if game.strip()])
            # Adiciona keywords fixas se quiser
            keywords_base.extend(["furia", "counter-strike", "csgo", "cs2"]) # Exemplo
            keywords_unique = list(set(filter(None, keywords_base))) # Remove vazios e duplicatas
            logger.info(f"Keywords para validação de links: {keywords_unique}")

            # Pega as URLs da caixa de texto (uma por linha)
            urls_to_check = [url.strip() for url in raw_links_text.splitlines() if url.strip().startswith(('http://', 'https://'))]

            if urls_to_check:
                logger.info(f"Validando {len(urls_to_check)} links...")
                # Cria tarefas para validar cada URL concorrentemente
                validation_tasks = [validate_esports_link(url, keywords_unique) for url in urls_to_check]
                # Executa as tarefas e pega os resultados (strings de status)
                results = await asyncio.gather(*validation_tasks)

                # Formata o texto final para salvar no DB
                validation_summary = []
                for url, status in zip(urls_to_check, results):
                    validation_summary.append(f"• {url}: {status}")
                validation_results_text = "\n".join(validation_summary)
                logger.info("Validação de links concluída.")
            else:
                logger.info("Nenhuma URL válida encontrada no campo de links.")
                validation_results_text = "Nenhuma URL válida fornecida."

        # Salva o resultado da validação no perfil
        profile.esports_links_validation = validation_results_text
        # --- <<< FIM LÓGICA VALIDAÇÃO LINKS >>> ---


        # Salva tudo no DB
        try:
            db.session.commit()
            logger.info("Alterações salvas no DB (incluindo links/validação).")
            flash(f'Perfil {"criado" if was_new else "atualizado"} com sucesso!', 'success')
            return redirect(url_for('view_profile'))
        except Exception as e:
            db.session.rollback()
            logger.exception("ERRO ao commitar alterações no DB")
            flash(f'Erro ao salvar perfil no banco de dados.', 'danger')

    # Renderiza form em caso de GET ou falha na validação do POST
    return render_template('edit_profile.html', form=form)


# --- Execução do App ---
if __name__ == '__main__':
    logger.info("Iniciando servidor de desenvolvimento Flask...")
    app.run(debug=True, host='0.0.0.0', port=5000) # Especifica a porta explicitamente