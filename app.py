from flask import Flask, session
from routes.main import main_bp
from routes.cart import cart_bp      # Importa o Blueprint do carrinho
from routes.auth import auth_bp      # Importa o Blueprint de autenticação
from routes.user import user_bp      # Importa o Blueprint do usuário
from routes.checkout import checkout_bp # IMPORTA O NOVO BLUEPRINT DE CHECKOUT
from routes.admin import admin_bp # Importa o Blueprint de administração
from database import inicializar_banco, contar_itens_carrinho_db
from config import Config # Importar Config para SECRET_KEY e DB_NAME

# 1. Cria a instância do aplicativo Flask
app = Flask(__name__)

# 2. Carrega as configurações do seu objeto Config
app.config.from_object(Config)

# 3. Inicializa o banco de dados
# Isso criará as tabelas se elas ainda não existirem
inicializar_banco()

# 4. Registra os Blueprints
# É fundamental registrar TODOS os blueprints que você criou
app.register_blueprint(main_bp)
app.register_blueprint(cart_bp)      # Registra o Blueprint do carrinho
app.register_blueprint(auth_bp)      # Registra o Blueprint de autenticação
app.register_blueprint(user_bp)      # Registra o Blueprint do usuário
app.register_blueprint(checkout_bp)  # REGISTRA O BLUEPRINT DE CHECKOUT AQUI!
app.register_blueprint(admin_bp) # Registra o Blueprint de administração

# 5. Processador de contexto para injetar dados globais nos templates
@app.context_processor
def inject_global_data():
    """
    Injeta o número total de itens no carrinho na sessão
    para ser acessível em todos os templates.
    """
    total_itens = 0
    # Verifica se o usuário está logado na sessão antes de tentar contar itens do carrinho
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        try:
            # Chama a função do database para contar os itens do carrinho
            total_itens = contar_itens_carrinho_db(usuario_id)
        except Exception as e:
            # Em caso de erro (ex: tabela não existe se DB não foi inicializado corretamente),
            # logar o erro e retornar 0 para não quebrar a aplicação.
            print(f"Erro ao contar itens do carrinho para o usuário {usuario_id}: {e}")
            total_itens = 0
    return {'total_itens': total_itens}

# 6. Bloco para rodar o aplicativo diretamente
if __name__ == '__main__':
    app.run(debug=True, port=5001)
