# app.py
import os
import logging
import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename
import asyncio
import httpx
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from typing import List  # Adicionado para type hint

# Carrega variáveis do .env
load_dotenv()

# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuração do App Flask
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "fallback-default-secret-key-CHANGE-ME"
)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///fan_profiles.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
    os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", "False").lower() == "true"
)
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
        logger.info(f"Pasta de uploads criada em: {os.path.abspath(UPLOAD_FOLDER)}")
    except OSError as e:
        logger.error(
            f"ERRO CRÍTICO: Falha ao criar pasta de uploads '{UPLOAD_FOLDER}': {e}"
        )
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Configuração Tesseract (Ajustar caminho se necessário)
TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # <<< AJUSTE SEU CAMINHO AQUI!!!
)
try:
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        tesseract_version = pytesseract.get_tesseract_version()
        logger.info(
            f"Tesseract OCR configurado manualmente para: {TESSERACT_PATH} (Versão: {tesseract_version})"
        )
    else:
        tesseract_version = pytesseract.get_tesseract_version()
        logger.info(
            f"Tesseract OCR encontrado automaticamente no PATH (Versão: {tesseract_version})."
        )
except Exception as e:
    logger.error(
        f"Tesseract OCR NÃO encontrado. Configure o caminho manualmente se o OCR falhar. Erro: {e}"
    )
    pytesseract.pytesseract.tesseract_cmd = None  # Define como None se não encontrar

# Inicializa extensões
from models import db

db.init_app(app)
csrf = CSRFProtect(app)

# Importa modelos e formulários
from models import FanProfile
from forms import ProfileForm

# Cria as tabelas no banco de dados
with app.app_context():
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    logger.info(f"Verificando/Criando banco de dados em: {db_uri}")
    try:
        db.create_all()
        logger.info("Tabelas do banco de dados verificadas/criadas com sucesso.")
    except Exception as e:
        logger.exception(f"ERRO CRÍTICO ao verificar/criar tabelas para URI '{db_uri}'")


# --- Função Auxiliar: Validador de Link (Simulado com Keywords) ---
async def validate_esports_link(url: str, keywords: List[str]) -> str:
    """Tenta buscar o conteúdo de uma URL e verifica se contém keywords."""
    if not url.startswith(("http://", "https://")):
        return "Inválido (URL mal formatada)"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    status = "Não verificado (Erro)"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            logger.info(f"Validando link: {url}")
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type:
                logger.warning(f"Link {url} não é HTML ({content_type}).")
                return f"Não verificado (Não é HTML)"
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text(" ", strip=True).lower()
            found_keyword = any(
                keyword in page_text for keyword in keywords if keyword
            )  # Verifica se keyword não é vazia
            status = (
                "Relevante (Keyword encontrada)"
                if found_keyword
                else "Não Relevante (Keyword não encontrada)"
            )
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


# --- Rotas (Páginas) da Aplicação ---
@app.route("/")
def view_profile():
    """Exibe o perfil do fã (ID=1)."""
    profile = None
    try:
        profile = db.session.get(FanProfile, 1)
        if not profile:
            logger.info("Perfil ID=1 não encontrado no DB ao carregar a view.")
            flash("Nenhum perfil encontrado (ID=1). Crie um!", "info")
            return redirect(url_for("edit_profile"))
        logger.info(f"Renderizando profile.html para {profile.name}")
        return render_template("profile.html", profile=profile)
    except Exception as e:
        logger.exception(f"Erro ao buscar perfil ID=1 no DB para view")
        flash("Erro ao acessar o banco de dados.", "danger")
        return redirect(url_for("edit_profile"))


@app.route("/edit", methods=["GET", "POST"])
async def edit_profile():  # Rota continua async por causa da validação de links
    """Exibe o formulário para criar/editar o perfil (ID=1) e processa."""
    profile = db.session.get(FanProfile, 1)
    form = ProfileForm(obj=profile)

    if form.validate_on_submit():
        was_new = False
        if profile is None:
            profile = FanProfile(id=1)
            db.session.add(profile)
            was_new = True

        # Salva links ANTES de populate para pegar o valor bruto da textarea
        raw_links_text = form.esports_profile_links.data
        # Popula todos os campos (incluindo os novos de redes sociais)
        form.populate_obj(profile)
        # Atribui o valor bruto dos links depois do populate_obj ter limpado
        profile.esports_profile_links = raw_links_text

        logger.info(
            f"Objeto FanProfile {'novo' if was_new else 'existente'} populado com dados do form."
        )

        # Lógica de Upload e OCR (como antes)
        file = form.document.data
        if file:
            try:
                filename = secure_filename(
                    f"profile_{profile.id or 'new'}_doc{os.path.splitext(file.filename)[1]}"
                )
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)
                profile.uploaded_doc_filename = filename
                logger.info(f"Arquivo '{filename}' salvo.")
                if (
                    pytesseract.pytesseract.tesseract_cmd
                    or pytesseract.get_tesseract_version()
                ):  # Verifica se Tesseract está ok
                    try:
                        logger.info(f"Tentando OCR no arquivo: {save_path}")
                        ocr_text = pytesseract.image_to_string(
                            Image.open(save_path), lang="por", timeout=15
                        )
                        profile.doc_ocr_result = (
                            ocr_text.strip() if ocr_text else "OCR não encontrou texto."
                        )
                        logger.info(
                            f"OCR concluído. Texto (início): {profile.doc_ocr_result[:100]}"
                        )
                    except pytesseract.TesseractNotFoundError:
                        logger.error(
                            "ERRO OCR: Tesseract não encontrado durante execução."
                        )
                        profile.doc_ocr_result = "ERRO: Tesseract OCR não configurado."
                    except Exception as ocr_error:
                        logger.error(
                            f"ERRO OCR: Falha ao processar imagem: {ocr_error}",
                            exc_info=True,
                        )
                        profile.doc_ocr_result = f"Erro durante OCR: {ocr_error}"
                else:
                    logger.warning(
                        "OCR não executado pois Tesseract não foi encontrado/configurado."
                    )
                    profile.doc_ocr_result = "OCR não disponível."
            except Exception as upload_error:
                logger.error(
                    f"Erro durante upload/salvamento do arquivo: {upload_error}",
                    exc_info=True,
                )
                flash(f"Erro ao fazer upload do arquivo.", "danger")
                profile.uploaded_doc_filename = None
                profile.doc_ocr_result = None
        else:
            logger.info("Nenhum arquivo enviado para o campo 'document'.")

        # Lógica de Validar Links E-sports (como antes)
        validation_results_text = "Nenhum link fornecido."
        if raw_links_text:
            keywords_base = []
            if profile.favorite_teams:
                keywords_base.extend(
                    [
                        t.strip().lower()
                        for t in profile.favorite_teams.split(",")
                        if t.strip()
                    ]
                )
            if profile.favorite_games:
                keywords_base.extend(
                    [
                        g.strip().lower()
                        for g in profile.favorite_games.split(",")
                        if g.strip()
                    ]
                )
            keywords_base.extend(["furia", "counter-strike", "csgo", "cs2"])
            keywords_unique = list(set(filter(None, keywords_base)))
            logger.info(f"Keywords para validação de links: {keywords_unique}")
            urls_to_check = [
                url.strip()
                for url in raw_links_text.splitlines()
                if url.strip().startswith(("http://", "https://"))
            ]
            if urls_to_check:
                logger.info(f"Validando {len(urls_to_check)} links...")
                validation_tasks = [
                    validate_esports_link(url, keywords_unique) for url in urls_to_check
                ]
                results = await asyncio.gather(*validation_tasks)
                validation_summary = [
                    f"• {url}: {status}" for url, status in zip(urls_to_check, results)
                ]
                validation_results_text = "\n".join(validation_summary)
                logger.info("Validação de links concluída.")
            else:
                logger.info("Nenhuma URL válida encontrada no campo de links.")
                validation_results_text = "Nenhuma URL válida fornecida."
        else:
            logger.info("Campo de links de perfil e-sports estava vazio.")
            validation_results_text = "Nenhum link informado."

        profile.esports_links_validation = validation_results_text

        # Salva tudo no DB
        try:
            db.session.commit()
            logger.info("Alterações salvas no DB.")
            flash(
                f'Perfil {"criado" if was_new else "atualizado"} com sucesso!',
                "success",
            )
            return redirect(url_for("view_profile"))
        except Exception as e:
            db.session.rollback()
            logger.exception("ERRO ao commitar alterações no DB")
            flash(f"Erro ao salvar perfil no banco de dados.", "danger")

    # Renderiza form em caso de GET ou falha na validação do POST
    return render_template("edit_profile.html", form=form)


# --- Execução do App ---
if __name__ == "__main__":
    logger.info("Iniciando servidor de desenvolvimento Flask...")
    app.run(debug=True, host="0.0.0.0", port=5000)
