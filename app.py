from flask import Flask, render_template, session, flash, redirect, url_for, abort, jsonify
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename

# Importar configurações
from config import Config

# Importar funções do banco de dados
from database import conectar_db, inicializar_banco, contar_itens_carrinho_db

# Importar utilitários
from utils.helpers import allowed_file, formatar_moeda # Se precisar delas aqui, senão, remova
from utils.decorators import login_required, admin_required # Se precisar delas aqui para Context Processor, senão remova

# Importar Blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.cart import cart_bp
from routes.checkout import checkout_bp
from routes.user import user_bp
from routes.admin import admin_bp

# --- Flask App Instance and Configuration ---
app = Flask(__name__)
app.config.from_object(Config) # Carrega as configurações do objeto Config

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Context Processor (single definition) ---
@app.context_processor
def inject_carrinho():
    total_itens = 0
    if 'usuario_id' in session:
        try:
            total_itens = contar_itens_carrinho_db(session['usuario_id'])
        except Exception as e:
            print(f"Erro no context processor ao contar itens do carrinho (DB): {e}")
            total_itens = 0
    return {'total_itens': total_itens, 'formatar_moeda': formatar_moeda} # Adiciona formatar_moeda para uso em templates

# --- Registrar Blueprints ---
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(checkout_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp) # O admin_bp já tem url_prefix='/admin'

# --- Main entry point ---
if __name__ == '__main__':
    inicializar_banco() # Inicializa o banco de dados na primeira execução
    app.run(debug=True, port=5001)