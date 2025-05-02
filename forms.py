# forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
# <<< Importar URL se já não estiver >>>
from wtforms.validators import DataRequired, Email, Optional, URL

class ProfileForm(FlaskForm):
    """Formulário para editar o perfil do fã."""
    name = StringField('Nome Completo', validators=[DataRequired(message="Nome é obrigatório.")])
    email = StringField('Email', validators=[Optional(), Email(message="Email inválido.")])
    city = StringField('Cidade')
    state = StringField('Estado (UF)')
    favorite_teams = StringField('Times Favoritos (separados por vírgula)', render_kw={"placeholder": "Ex: FURIA, Liquid, FaZe"})
    favorite_games = StringField('Jogos Favoritos (separados por vírgula)', render_kw={"placeholder": "Ex: CSGO, CS2, Valorant"})
    esports_interests = TextAreaField('Interesses em E-sports (descreva)')
    last_year_activities = TextAreaField('Atividades/Compras/Eventos de E-sports (último ano)')
    document = FileField(
        'Enviar Documento Placeholder (Imagem JPG/PNG)',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'png', 'jpeg'], 'Apenas imagens JPG ou PNG são permitidas!')
        ]
    )
    esports_profile_links = TextAreaField(
        'Links de Perfis E-sports (um por linha)',
        render_kw={"placeholder": "https://www.hltv.org/player/123/nickname\nhttps://liquipedia.net/counterstrike/Player_Name"}
        )

    # --- Campos Sociais ---
    twitter_url = StringField(
        'Perfil Twitter (URL Completa)',
        validators=[Optional(), URL(message='URL inválida.')],
        render_kw={"placeholder": "https://twitter.com/seu_usuario"}
    )
    twitch_url = StringField(
        'Canal Twitch (URL Completa)',
        validators=[Optional(), URL(message='URL inválida.')],
        render_kw={"placeholder": "https://twitch.tv/seu_canal"}
    )
    # <<< NOVOS CAMPOS ADICIONADOS (Facebook, Instagram, TikTok) >>>
    facebook_url = StringField(
        'Perfil Facebook (URL Completa)',
        validators=[Optional(), URL(message='URL inválida.')],
        render_kw={"placeholder": "https://facebook.com/seu.perfil"}
    )
    instagram_url = StringField(
        'Perfil Instagram (URL Completa)',
        validators=[Optional(), URL(message='URL inválida.')],
        render_kw={"placeholder": "https://instagram.com/seu_usuario"}
    )
    tiktok_url = StringField(
        'Perfil TikTok (URL Completa)',
        validators=[Optional(), URL(message='URL inválida.')],
         render_kw={"placeholder": "https://tiktok.com/@seu_usuario"}
    )

    submit = SubmitField('Salvar Perfil')