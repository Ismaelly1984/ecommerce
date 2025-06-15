from config import Config
from werkzeug.utils import secure_filename

def allowed_file(filename):
    """
    Verifica se a extensão do arquivo é permitida para upload,
    utilizando as extensões definidas em Config.ALLOWED_EXTENSIONS.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def formatar_moeda(valor):
    """
    Formata um valor numérico para o formato de moeda brasileira (R$ X.XXX,XX).
    """
    # Garante que o valor é formatado com 2 casas decimais e usa vírgula como separador decimal
    return f"R$ {valor:.2f}".replace('.', ',')