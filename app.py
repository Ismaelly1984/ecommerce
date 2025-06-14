from flask import Flask, session, flash, redirect, url_for, jsonify
import os

# Importar configurações
from config import Config

# Importar funções do banco de dados
from database import conectar_db, inicializar_banco, contar_itens_carrinho_db

# Importar utilitários
from utils.helpers import formatar_moeda # Mantido para o context processor

# Importar Blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.cart import cart_bp
from routes.checkout import checkout_bp
from routes.user import user_bp
from routes.admin import admin_bp

# --- DEFINIÇÃO DA FUNÇÃO create_app() ---
# Esta função cria e configura a instância do seu aplicativo Flask.
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) # Carrega as configurações do objeto Config

    # Criar pasta de uploads se não existir
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- Context Processor (para disponibilizar total_itens e formatar_moeda globalmente) ---
    @app.context_processor
    def inject_carrinho():
        total_itens = 0
        if 'usuario_id' in session:
            try:
                total_itens = contar_itens_carrinho_db(session['usuario_id'])
            except Exception as e:
                print(f"Erro no context processor ao contar itens do carrinho (DB direto): {e}")
                total_itens = 0
        return {'total_itens': total_itens, 'formatar_moeda': formatar_moeda}

    # --- Registrar Blueprints ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp) # O admin_bp já tem url_prefix='/admin'

    return app # Retorna a instância do aplicativo configurada

# --- Main entry point ---
if __name__ == '__main__':
    # Inicializa o banco de dados (cria tabelas e insere admin, se aplicável)
    # Isso é feito uma vez quando você inicia a aplicação diretamente
    inicializar_banco()

    # Cria a instância da aplicação usando a fábrica
    app_instance = create_app() # Chame a função create_app() aqui

    # Inicia o servidor Flask usando a instância retornada
    app_instance.run(debug=True, port=5001)