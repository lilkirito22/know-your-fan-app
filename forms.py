# forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed # <<< Importa FileField e FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Optional

class ProfileForm(FlaskForm):
    """Formulário para editar o perfil do fã."""
    name = StringField('Nome Completo', validators=[DataRequired(message="Nome é obrigatório.")])
    email = StringField('Email', validators=[Optional(), Email(message="Email inválido.")])
    city = StringField('Cidade')
    state = StringField('Estado (UF)')
    favorite_teams = StringField('Times Favoritos (separados por vírgula)')
    favorite_games = StringField('Jogos Favoritos (separados por vírgula)')
    esports_interests = TextAreaField('Interesses em E-sports (descreva)')
    last_year_activities = TextAreaField('Atividades/Compras/Eventos de E-sports (último ano)')

    # <<< NOVO CAMPO ADICIONADO >>>
    document = FileField(
        'Enviar Documento Placeholder (Imagem JPG/PNG)',
        validators=[
            Optional(), # Permite não enviar arquivo
            FileAllowed(['jpg', 'png', 'jpeg'], 'Apenas imagens JPG ou PNG são permitidas!')
        ]
    )
    esports_profile_links = TextAreaField('Links de Perfis E-sports (HLTV, Liquipedia, etc. - um por linha)')

    submit = SubmitField('Salvar Perfil')