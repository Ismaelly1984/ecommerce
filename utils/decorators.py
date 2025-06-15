from functools import wraps
from flask import session, flash, redirect, url_for, abort

def login_required(f):
    """
    Decorador que exige que o usuário esteja logado para acessar a rota.
    Redireciona para a página de login se não estiver autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            # Mensagem flash com tipo 'warning' para informar ao usuário que o login é necessário.
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            # Redireciona para a rota de login do blueprint 'auth'.
            return redirect(url_for('auth.login')) 
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador que exige que o usuário seja um administrador logado para acessar a rota.
    Redireciona ou retorna 403 (Forbidden) se não for um administrador.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se o usuário está logado E se possui o status de administrador.
        # Usa .get('is_admin', False) para evitar KeyError se 'is_admin' não estiver na sessão.
        if 'usuario_id' not in session or not session.get('is_admin', False):
            # Mensagem flash com tipo 'danger' para indicar acesso negado.
            flash('Acesso restrito a administradores. Você não tem permissão para acessar esta página.', 'danger')
            # Redireciona para a página de login. Você pode mudar para abort(403) ou url_for('main.home')
            # dependendo da experiência de usuário desejada para acesso negado.
            return redirect(url_for('auth.login')) 
        return f(*args, **kwargs)
    return decorated_function