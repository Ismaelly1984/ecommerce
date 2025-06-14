from config import Config
from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def formatar_moeda(valor):
    return f"R$ {valor:.2f}".replace('.', ',')