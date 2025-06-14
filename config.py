import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua_chave_secreta_muito_longa_e_aleatoria_aqui' # Use env var in production!
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    DB_NAME = 'ecommerce.db'
    # Adicione outras configurações aqui, se necessário