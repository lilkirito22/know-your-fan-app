# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class FanProfile(db.Model):
    """Modelo para armazenar o perfil do fã."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    favorite_teams = db.Column(db.Text, nullable=True)
    favorite_games = db.Column(db.Text, nullable=True)
    esports_interests = db.Column(db.Text, nullable=True)
    last_year_activities = db.Column(db.Text, nullable=True)
    esports_profile_links = db.Column(db.Text, nullable=True)
    esports_links_validation = db.Column(db.Text, nullable=True)

    # <<< NOVAS COLUNAS ADICIONADAS >>>
    uploaded_doc_filename = db.Column(db.String(255), nullable=True) # Nome do arquivo placeholder salvo
    doc_ocr_result = db.Column(db.Text, nullable=True) # Resultado do OCR simulado ou status

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<FanProfile {self.name} (ID: {self.id})>'