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
def edit_profile():
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

        # Popula dados normais (exceto arquivo)
        form.populate_obj(profile)
        logger.info(f"Objeto FanProfile populado com dados do form (exceto arquivo).")


        # --- <<< LÓGICA DE UPLOAD E OCR ADICIONADA >>> ---
        file = form.document.data # Pega o objeto do arquivo do WTForms
        if file: # Se um arquivo foi enviado
            try:
                # 1. Salvar o Arquivo
                # Usamos o ID do perfil para garantir nome único simples neste caso
                filename = secure_filename(f"profile_{profile.id or 'new'}_doc{os.path.splitext(file.filename)[1]}")
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                logger.info(f"Arquivo '{filename}' salvo em '{save_path}'")
                profile.uploaded_doc_filename = filename # Guarda nome no DB

                # 2. Tentar OCR (Simulação de IA)
                logger.info(f"Tentando OCR no arquivo: {save_path}")
                # Verifica se o Tesseract foi encontrado na inicialização
                if pytesseract.pytesseract.tesseract_cmd or pytesseract.get_tesseract_version():
                     try:
                         # Tenta OCR em português
                         ocr_text = pytesseract.image_to_string(Image.open(save_path), lang='por', timeout=15)
                         profile.doc_ocr_result = ocr_text.strip() if ocr_text else "OCR não encontrou texto na imagem."
                         logger.info(f"OCR concluído. Texto (início): {profile.doc_ocr_result[:100]}")
                     except pytesseract.TesseractNotFoundError:
                          logger.error("ERRO OCR: Executável Tesseract não foi encontrado durante a execução. Verifique a configuração.")
                          profile.doc_ocr_result = "ERRO: Tesseract OCR não configurado/encontrado."
                     except Exception as ocr_error:
                          logger.error(f"ERRO OCR: Falha ao processar imagem: {ocr_error}", exc_info=True)
                          profile.doc_ocr_result = f"Erro durante OCR: {ocr_error}"
                else:
                     logger.warning("OCR não executado pois Tesseract não foi encontrado na inicialização.")
                     profile.doc_ocr_result = "OCR não disponível (Tesseract não encontrado)."


            except Exception as upload_error:
                 logger.error(f"Erro durante upload/salvamento do arquivo: {upload_error}", exc_info=True)
                 flash(f"Erro ao fazer upload do arquivo.", 'danger')
                 # Limpa campos relacionados ao arquivo se o upload falhar
                 profile.uploaded_doc_filename = None
                 profile.doc_ocr_result = None
        else:
            logger.info("Nenhum arquivo enviado para o campo 'document'.")
            # Se nenhum arquivo foi enviado, não alteramos os campos existentes no DB
            # profile.uploaded_doc_filename = profile.uploaded_doc_filename # Mantém o valor antigo
            # profile.doc_ocr_result = profile.doc_ocr_result # Mantém o valor antigo
        # --- <<< FIM LÓGICA UPLOAD E OCR >>> ---

        # Salva tudo no DB
        try:
            db.session.commit()
            logger.info("Alterações salvas no DB.")
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