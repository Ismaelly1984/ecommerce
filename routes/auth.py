from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import conectar_db, registrar_log
from utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        senha_hash = generate_password_hash(senha)

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha_hash))
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login')) # Redirecionar para rota do blueprint
        except sqlite3.IntegrityError:
            flash('Este email já está cadastrado.', 'danger')

    return render_template('cadastro.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute('SELECT id, nome, senha, is_admin FROM usuarios WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['senha'], senha):
            session['usuario_id'] = user['id']
            session['usuario_nome'] = user['nome']
            session['is_admin'] = bool(user['is_admin'])

            registrar_log(user['id'], 'login') # Usar função do database.py

            conn.close()

            if user['is_admin']:
                return redirect(url_for('admin.admin_dashboard')) # Redirecionar para blueprint admin
            return redirect(url_for('main.home')) # Redirecionar para blueprint main

        conn.close()
        flash('Usuário ou senha incorretos', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required # Logout exige login prévio
def logout():
    registrar_log(session.get('usuario_id'), 'logout') # Registrar logout
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login')) # Redirecionar para rota do blueprint