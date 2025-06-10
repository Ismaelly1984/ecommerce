from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename

# --- Flask App Instance and Configuration ---
app = Flask(__name__)
# IMPORTANT: Use a strong, unique secret key!
app.config['SECRET_KEY'] = 'sua_chave_secreta_muito_longa_e_aleatoria_aqui' 
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def calcular_total_carrinho():
    try:
        # This function likely needs to be updated to query the database cart
        # if you fully transition to a database-only cart for logged-in users.
        # For now, it might be used by session-based carts if not logged in.
        return sum(float(item['preco']) * int(item['quantidade'])
                 for item in session.get('carrinho', []))
    except (KeyError, TypeError, ValueError):
        return 0.0

def formatar_moeda(valor):
    return f"R$ {valor:.2f}".replace('.', ',')

DB_NAME = 'ecommerce.db'

def conectar_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def inicializar_banco():
    conn = conectar_db() # Use the consistent conectar_db
    cursor = conn.cursor()

    # Create tables
    # Ensure 'usuarios' table creation is only once and matches other definitions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carrinho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 1,
            data_adicionado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL,
            descricao TEXT,
            imagem TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Pendente',
            total REAL DEFAULT 0.0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedido_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_atividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            acao TEXT NOT NULL,
            detalhes TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # Add admin user if not exists
    cursor.execute('SELECT COUNT(*) FROM usuarios WHERE is_admin = 1')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('Admin', 'admin@example.com', generate_password_hash('admin123'), 1))
        conn.commit()
        print("Admin user created.")


# --- Database Cart Operations (used by routes and context processor) ---
def contar_itens_carrinho_db(usuario_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT COALESCE(SUM(quantidade), 0)
    FROM carrinho
    WHERE usuario_id = ?
    ''', (usuario_id,))
    total_itens = cursor.fetchone()[0]
    conn.close()
    return total_itens

def adicionar_ao_carrinho_db(usuario_id, produto_id, quantidade=1):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT quantidade FROM carrinho
    WHERE usuario_id = ? AND produto_id = ?
    ''', (usuario_id, produto_id))
    item = cursor.fetchone()
    if item:
        nova_quantidade = item[0] + quantidade
        cursor.execute('''
        UPDATE carrinho SET quantidade = ?
        WHERE usuario_id = ? AND produto_id = ?
        ''', (nova_quantidade, usuario_id, produto_id))
    else:
        cursor.execute('''
        INSERT INTO carrinho (usuario_id, produto_id, quantidade)
        VALUES (?, ?, ?)
        ''', (usuario_id, produto_id, quantidade))
    conn.commit()
    conn.close()

def remover_do_carrinho_db(usuario_id, produto_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM carrinho
    WHERE usuario_id = ? AND produto_id = ?
    ''', (usuario_id, produto_id))
    conn.commit()
    conn.close()

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
    # No 'elif carrinho in session' here if all cart ops are login_required and DB-based.
    # If you intend to have a temporary session cart for guests, that logic needs to be robust.
    return {'total_itens': total_itens}

# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session or not session.get('is_admin', False):
            flash('Acesso restrito a administradores', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def home(): # <-- Agora é 'home'!
    pagina = request.args.get('pagina', 1, type=int)
    produtos_por_pagina = 10

    conn = conectar_db()
    cursor = conn.cursor()

    offset = (pagina - 1) * produtos_por_pagina
    cursor.execute('''
        SELECT * FROM produtos
        LIMIT ? OFFSET ?
    ''', (produtos_por_pagina, offset))
    produtos = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) FROM produtos')
    total_produtos = cursor.fetchone()[0]
    tem_mais = (offset + produtos_por_pagina) < total_produtos

    conn.close()
    return render_template('index.html', produtos=produtos, pagina=pagina, tem_mais=tem_mais)

@app.route('/produto/<int:id>')
def detalhes_produto(id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos WHERE id = ?', (id,))
    produto = cursor.fetchone()
    conn.close()

    if produto is None:
        abort(404)

    produto_dict = {
        'id': produto['id'], # Access by name
        'nome': produto['nome'],
        'preco': produto['preco'],
        'estoque': produto['estoque'],
        'descricao': produto['descricao'],
        'imagem': produto['imagem']
    }
    return render_template('detalhes_produto.html', produto=produto_dict)

@app.route('/carregar-mais-produtos')
def carregar_mais_produtos():
    pagina = request.args.get('pagina', 1, type=int)
    produtos_por_pagina = 10
    offset = (pagina - 1) * produtos_por_pagina

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM produtos
        LIMIT ? OFFSET ?
    ''', (produtos_por_pagina, offset))
    produtos = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) FROM produtos')
    total_produtos = cursor.fetchone()[0]
    tem_mais = (offset + produtos_por_pagina) < total_produtos

    conn.close()

    # You might want to render only a partial HTML for new products,
    # not the full index.html. This example assumes index.html can handle it.
    # A more robust solution for AJAX would be a dedicated template for product cards.
    produtos_html = render_template('partials/product_cards.html', produtos=produtos) # Example of a partial

    return jsonify({
        'html': produtos_html,
        'tem_mais': tem_mais,
        'proxima_pagina': pagina + 1
    })

@app.route('/cadastro', methods=['GET', 'POST'])
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
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Este email já está cadastrado.', 'danger')

    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        conn = conectar_db()
        cursor = conn.cursor() # conn.row_factory is set in conectar_db now

        cursor.execute('SELECT id, nome, senha, is_admin FROM usuarios WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['senha'], senha):
            session['usuario_id'] = user['id']
            session['usuario_nome'] = user['nome']
            session['is_admin'] = bool(user['is_admin'])

            cursor.execute('''
                INSERT INTO logs_atividades (usuario_id, acao)
                VALUES (?, ?)
            ''', (user['id'], 'login'))

            conn.commit()
            conn.close()

            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home')) # Corrected: 'home' to 'index'

        conn.close()
        flash('Usuário ou senha incorretos', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login')) # Redirect to index after logout

@app.route('/adicionar_ao_carrinho/<int:produto_id>', methods=['POST']) # Use POST for state-changing actions
@login_required
def adicionar_ao_carrinho(produto_id):
    try:
        # Check product existence and stock (important!)
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('SELECT nome, estoque FROM produtos WHERE id = ?', (produto_id,))
        produto_info = cursor.fetchone()
        conn.close()

        if not produto_info:
            flash('Produto não encontrado.', 'danger')
            return redirect(request.referrer or url_for('home'))

        if produto_info['estoque'] < 1:
            flash(f'Produto "{produto_info["nome"]}" está fora de estoque.', 'danger')
            return redirect(request.referrer or url_for('home'))

        adicionar_ao_carrinho_db(session['usuario_id'], produto_id, 1) # Use the DB function
        flash('Produto adicionado ao carrinho!', 'success')
    except Exception as e:
        flash(f'Erro ao adicionar produto ao carrinho: {e}', 'danger')
        print(f"Error adding to cart: {e}")
    return redirect(request.referrer or url_for('home')) # Redirect back or to index

@app.route('/remover_do_carrinho/<int:produto_id>', methods=['POST']) # Use POST for state-changing actions
@login_required
def remover_do_carrinho(produto_id):
    try:
        remover_do_carrinho_db(session['usuario_id'], produto_id) # Use the DB function
        flash('Produto removido do carrinho.', 'info')
    except Exception as e:
        flash(f'Erro ao remover produto do carrinho: {e}', 'danger')
        print(f"Error removing from cart: {e}")
    return redirect(url_for('ver_carrinho'))

@app.route('/carrinho')
@login_required
def ver_carrinho():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT p.id, p.nome, p.preco, c.quantidade, p.imagem
    FROM carrinho c
    JOIN produtos p ON c.produto_id = p.id
    WHERE c.usuario_id = ?
    ''', (session['usuario_id'],))

    itens = cursor.fetchall() # Already dict-like due to row_factory
    conn.close()

    total = sum(item['preco'] * item['quantidade'] for item in itens)
    return render_template('carrinho.html', carrinho=itens, total=total)

@app.route('/finalizar-compra', methods=['POST'])
@login_required # Ensure user is logged in
def finalizar_compra():
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # Get cart items from DB for current user
        cursor.execute('''
            SELECT c.produto_id, c.quantidade, p.preco, p.estoque, p.nome
            FROM carrinho c
            JOIN produtos p ON c.produto_id = p.id
            WHERE c.usuario_id = ?
        ''', (session['usuario_id'],))
        carrinho_db_items = cursor.fetchall()

        if not carrinho_db_items:
            flash('Seu carrinho está vazio', 'danger')
            conn.close()
            return redirect(url_for('ver_carrinho'))

        total = sum(item['preco'] * item['quantidade'] for item in carrinho_db_items)

        # 1. Create the order
        cursor.execute('''
            INSERT INTO pedidos (usuario_id, data, status, total)
            VALUES (?, datetime('now'), 'Processando', ?)
        ''', (session['usuario_id'], total))
        pedido_id = cursor.lastrowid

        # 2. Insert order items and update stock
        for item in carrinho_db_items:
            produto_id = item['produto_id']
            quantidade_no_carrinho = item['quantidade']
            preco_unitario = item['preco']
            estoque_disponivel = item['estoque']
            produto_nome = item['nome']

            if quantidade_no_carrinho > estoque_disponivel:
                conn.rollback()
                flash(f'Estoque insuficiente para o produto "{produto_nome}". Disponível: {estoque_disponivel}, No carrinho: {quantidade_no_carrinho}', 'danger')
                conn.close()
                return redirect(url_for('ver_carrinho'))

            cursor.execute('''
                INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
            ''', (pedido_id, produto_id, quantidade_no_carrinho, preco_unitario))

            cursor.execute('''
                UPDATE produtos
                SET estoque = estoque - ?
                WHERE id = ?
            ''', (quantidade_no_carrinho, produto_id))

        # Log the purchase
        cursor.execute('''
            INSERT INTO logs_atividades (usuario_id, acao, detalhes)
            VALUES (?, ?, ?)
        ''', (session['usuario_id'], 'finalizou compra', f'Pedido ID: {pedido_id}, Total: {total}'))

        # 3. Clear the user's cart in the database
        cursor.execute('DELETE FROM carrinho WHERE usuario_id = ?', (session['usuario_id'],))

        conn.commit()
        flash('Compra finalizada com sucesso!', 'success')
        return redirect(url_for('confirmacao_pedido', pedido_id=pedido_id)) # Redirect to confirmation page

    except Exception as e:
        conn.rollback()
        flash('Erro ao finalizar a compra. Tente novamente.', 'danger')
        print(f"Erro ao finalizar compra: {e}")
        return redirect(url_for('ver_carrinho'))
    finally:
        conn.close()

@app.route('/buscar', methods=['GET'])
def buscar_produtos():
    termo_busca = request.args.get('q', '').strip()

    if not termo_busca:
        return redirect(url_for('home')) # Redirect to index, not home

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT * FROM produtos
            WHERE LOWER(nome) LIKE LOWER(?) OR LOWER(descricao) LIKE LOWER(?)
            ORDER BY nome
        ''', (f'%{termo_busca}%', f'%{termo_busca}%'))

        produtos = cursor.fetchall()

        if not produtos:
            flash(f'Nenhum produto encontrado para "{termo_busca}"', 'info')
            # You might want to render index.html with an empty product list and the flash message
            return render_template('index.html', produtos=[], termo_busca=termo_busca) # Or redirect to index
            # return redirect(url_for('index'))

    except Exception as e:
        flash(f'Erro ao buscar produtos: {str(e)}', 'danger')
        return redirect(url_for('home')) # Redirect to index

    finally:
        conn.close()

    return render_template('index.html', produtos=produtos, termo_busca=termo_busca)


@app.route('/historico-pedidos')
@login_required # Ensure user is logged in
def historico_pedidos():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, data, status, total
        FROM pedidos
        WHERE usuario_id = ?
        ORDER BY data DESC
    ''', (session['usuario_id'],))

    pedidos = cursor.fetchall()

    historico = []
    for pedido in pedidos:
        cursor.execute('''
            SELECT pi.quantidade, pi.preco_unitario, pr.nome, pr.imagem
            FROM pedido_itens pi
            JOIN produtos pr ON pi.produto_id = pr.id
            WHERE pi.pedido_id = ?
        ''', (pedido['id'],)) # Access by name

        itens = []
        for item in cursor.fetchall():
            itens.append({
                'quantidade': item['quantidade'],
                'preco_unitario': item['preco_unitario'],
                'nome': item['nome'],
                'imagem': item['imagem']
            })

        historico.append({
            'id': pedido['id'],
            'data': pedido['data'],
            'status': pedido['status'],
            'total': pedido['total'],
            'itens': itens
        })

    conn.close()
    return render_template('historico_pedidos.html', historico=historico)

@app.route('/confirmacao-pedido/<int:pedido_id>')
@login_required # Ensure user is logged in
def confirmacao_pedido(pedido_id):
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, data, status, total
        FROM pedidos
        WHERE id = ? AND usuario_id = ?
    ''', (pedido_id, session['usuario_id']))

    pedido = cursor.fetchone()

    if not pedido:
        flash('Pedido não encontrado ou você não tem permissão para vê-lo.', 'danger')
        conn.close()
        return redirect(url_for('home'))

    cursor.execute('''
        SELECT pi.quantidade, pi.preco_unitario, pr.nome, pr.imagem
        FROM pedido_itens pi
        JOIN produtos pr ON pi.produto_id = pr.id
        WHERE pi.pedido_id = ?
    ''', (pedido_id,))

    itens = cursor.fetchall()
    conn.close()

    return render_template('confirmacao_pedido.html',
                         pedido={
                             'id': pedido['id'],
                             'data': pedido['data'],
                             'status': pedido['status'],
                             'total': pedido['total'],
                             'itens': itens # Itens are already dict-like
                         })

# --- Admin Routes ---
# admin_required decorator is defined correctly above.

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM produtos')
    total_produtos = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM usuarios')
    total_usuarios = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE DATE(data) = DATE('now', '-3 hours')") # Adjust for Brasil time if necessary
    pedidos_hoje = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos WHERE strftime('%Y-%m', data, '-3 hours') = strftime('%Y-%m', 'now', '-3 hours')")
    vendas_mensais = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    vendas_totais = cursor.fetchone()[0]

    cursor.execute('''
        SELECT p.id, u.nome as cliente, p.data, p.total, p.status
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.data DESC
        LIMIT 5
    ''')
    ultimos_pedidos = cursor.fetchall() # Already dict-like

    cursor.execute('SELECT nome, estoque FROM produtos WHERE estoque < 10 ORDER BY estoque ASC LIMIT 5')
    estoque_baixo = cursor.fetchall() # Already dict-like

    conn.close()

    return render_template('admin/dashboard.html',
                         total_produtos=total_produtos,
                         total_usuarios=total_usuarios,
                         pedidos_hoje=pedidos_hoje,
                         vendas_mensais=vendas_mensais,
                         vendas_totais=vendas_totais,
                         ultimos_pedidos=ultimos_pedidos,
                         estoque_baixo=estoque_baixo)


@app.route('/admin/produtos')
@admin_required
def admin_produtos():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM produtos ORDER BY nome')
    produtos = cursor.fetchall()

    conn.close()
    return render_template('admin/produtos.html', produtos=produtos)

@app.route('/admin/novo_produto', methods=['GET', 'POST'])
@admin_required
def novo_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])
        descricao = request.form['descricao']
        imagem_filename = None

        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagem_filename = filename

        conn = conectar_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO produtos (nome, preco, estoque, descricao, imagem)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, preco, estoque, descricao, imagem_filename))
            conn.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('admin_produtos'))
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao adicionar produto: {e}', 'danger')
        finally:
            conn.close()
    return render_template('admin/novo_produto.html')


@app.route('/admin/produtos/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_produto(id):
    conn = conectar_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])
        descricao = request.form['descricao']
        
        imagem_filename = request.form.get('imagem_existente') # Keep existing image if not uploaded new
        if 'imagem' in request.files and request.files['imagem'].filename != '':
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagem_filename = filename

        try:
            cursor.execute('''
                UPDATE produtos
                SET nome=?, preco=?, estoque=?, descricao=?, imagem=?
                WHERE id=?
            ''', (nome, preco, estoque, descricao, imagem_filename, id))

            conn.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('admin_produtos'))
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao atualizar produto: {e}', 'danger')
        finally:
            conn.close()
    else: # GET request
        cursor.execute('SELECT * FROM produtos WHERE id = ?', (id,))
        produto = cursor.fetchone()
        conn.close()

        if not produto:
            flash('Produto não encontrado', 'danger')
            return redirect(url_for('admin_produtos'))

        return render_template('admin/editar_produto.html', produto=produto)


@app.route('/admin/produtos/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_produto(id):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM produtos WHERE id = ?', (id,))
        conn.commit()
        flash('Produto excluído com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao excluir produto: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin_produtos'))

@app.route('/admin/pedidos')
@admin_required
def admin_pedidos():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.id, p.data, p.status, p.total, u.nome
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.data DESC
    ''')
    pedidos = cursor.fetchall()

    conn.close()
    return render_template('admin/pedidos.html', pedidos=pedidos)

@app.route('/admin/pedidos/<int:id>')
@admin_required
def detalhes_pedido(id):
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.id, p.data, p.status, p.total, u.nome, u.email
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        WHERE p.id = ?
    ''', (id,))
    pedido = cursor.fetchone()

    if not pedido:
        conn.close()
        flash('Pedido não encontrado', 'danger')
        return redirect(url_for('admin_pedidos'))

    cursor.execute('''
        SELECT pi.quantidade, pi.preco_unitario, pr.nome, pr.id
        FROM pedido_itens pi
        JOIN produtos pr ON pi.produto_id = pr.id
        WHERE pi.pedido_id = ?
    ''', (id,))
    itens = cursor.fetchall()

    conn.close()

    return render_template('admin/detalhes_pedido.html',
                         pedido=pedido,
                         itens=itens)

@app.route('/admin/pedidos/atualizar-status/<int:id>', methods=['POST'])
@admin_required
def atualizar_status_pedido(id):
    novo_status = request.form['status']

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE pedidos
            SET status = ?
            WHERE id = ?
        ''', (novo_status, id))

        conn.commit()
        flash('Status do pedido atualizado com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao atualizar status do pedido: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('detalhes_pedido', id=id))

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id, nome, email, is_admin FROM usuarios ORDER BY nome')
    usuarios = cursor.fetchall()

    conn.close()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@app.route('/admin/usuarios/toggle_admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin_status(user_id):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT is_admin FROM usuarios WHERE id = ?', (user_id,))
        current_status = cursor.fetchone()['is_admin']
        new_status = not bool(current_status)

        cursor.execute('UPDATE usuarios SET is_admin = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        flash(f'Status de administrador do usuário atualizado para {"Admin" if new_status else "Usuário Comum"}.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao alterar status de admin: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin_usuarios'))


@app.route('/admin/logs')
@admin_required
def admin_logs():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT l.id, l.acao, l.detalhes, l.data, u.nome
        FROM logs_atividades l
        LEFT JOIN usuarios u ON l.usuario_id = u.id
        ORDER BY l.data DESC
        LIMIT 100
    ''')
    logs = cursor.fetchall()

    conn.close()
    return render_template('admin/logs.html', logs=logs)

# --- Main entry point ---
if __name__ == '__main__':
    inicializar_banco()
    app.run(debug=True, port=5001)
