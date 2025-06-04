from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Troque para uma chave segura

def calcular_total_carrinho():
    try:
        return sum(float(item['preco']) * int(item['quantidade']) 
                 for item in session.get('carrinho', []))
    except (KeyError, TypeError, ValueError):
        return 0.0
    
def formatar_moeda(valor):
    return f"R$ {valor:.2f}".replace('.', ',')

DB_NAME = 'ecommerce.db'

def inicializar_banco():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Criar tabela de produtos se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL
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
    # Criar tabela de itens_pedido se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedido_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')        

    # Verifica se já existem produtos cadastrados
    cursor.execute('SELECT COUNT(*) FROM produtos')
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO produtos (nome, preco, estoque) VALUES ('Camiseta', 49.90, 100)")
        cursor.execute("INSERT INTO produtos (nome, preco, estoque) VALUES ('Calça Jeans', 129.90, 50)")

    # Criar tabela de usuários se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


def conectar_db():
    return sqlite3.connect(DB_NAME)

@app.route('/')
def home():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos)

@app.route('/produto/<int:id>')
def detalhes_produto(id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos WHERE id = ?', (id,))
    produto = cursor.fetchone()
    conn.close()
    
    if produto is None:
        abort(404)
    
    # Convertendo para dicionário para facilitar no template
    produto_dict = {
        'id': produto[0],
        'nome': produto[1],
        'preco': produto[2],
        'estoque': produto[3],
        'descricao': produto[4] if len(produto) > 4 else '',
        'imagem': produto[5] if len(produto) > 5 else None
    }
    
    return render_template('detalhes_produto.html', produto=produto_dict)
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_produto():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para adicionar produtos.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])
        
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', (nome, preco, estoque))
        conn.commit()
        conn.close()
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('home'))

    return render_template('adicionar.html')

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
        email = request.form['email']
        senha = request.form['senha']

        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario[3], senha):
            session['usuario_id'] = usuario[0]
            session['usuario_nome'] = usuario[1]
            flash(f'Bem-vindo, {usuario[1]}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email ou senha incorretos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('home'))

# Rota para adicionar ao carrinho (usando sessão)
@app.route('/adicionar_ao_carrinho/<int:produto_id>')
def adicionar_ao_carrinho(produto_id):
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    carrinho = session['carrinho']
    produto_no_carrinho = next((item for item in carrinho if item['produto_id'] == produto_id), None)
    
    if produto_no_carrinho:
        produto_no_carrinho['quantidade'] += 1
    else:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome, preco FROM produtos WHERE id = ?', (produto_id,))
        produto = cursor.fetchone()
        conn.close()
        
        if produto:
            carrinho.append({
                'produto_id': produto[0],
                'nome': produto[1],
                'preco': float(produto[2]),
                'quantidade': 1
            })
    
    session['carrinho'] = carrinho
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('home'))

@app.route('/carrinho')
def ver_carrinho():
    carrinho = session.get('carrinho', [])
    total = sum(item['preco'] * item['quantidade'] for item in carrinho)
    return render_template('carrinho.html', carrinho=carrinho, total=total)

@app.route('/remover_do_carrinho/<int:produto_id>')
def remover_do_carrinho(produto_id):
    if 'carrinho' in session:
        session['carrinho'] = [item for item in session['carrinho'] if item['produto_id'] != produto_id]
        flash('Produto removido do carrinho.', 'info')
    return redirect(url_for('ver_carrinho'))

@app.route('/finalizar-compra', methods=['POST'])
def finalizar_compra():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para finalizar a compra', 'warning')
        return redirect(url_for('login'))
    
    if 'carrinho' not in session or not session['carrinho']:
        flash('Seu carrinho está vazio', 'danger')
        return redirect(url_for('ver_carrinho'))
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Calcular total do carrinho
        total = sum(item['preco'] * item['quantidade'] for item in session['carrinho'])
        
        # 1. Criar o pedido no banco de dados
        cursor.execute('''
            INSERT INTO pedidos (usuario_id, data, status, total)
            VALUES (?, datetime('now'), 'Processando', ?)
        ''', (session['usuario_id'], total))
        
        pedido_id = cursor.lastrowid
        
        # 2. Adicionar itens do carrinho como itens do pedido
        for item in session['carrinho']:
            cursor.execute('''
                INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
            ''', (pedido_id, item['produto_id'], item['quantidade'], item['preco']))
        
        # 3. Limpar o carrinho da sessão
        session.pop('carrinho', None)
        
        conn.commit()
        conn.close()
        
        # Redirecionar para página de confirmação
        return redirect(url_for('confirmacao_pedido', pedido_id=pedido_id))
        
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao finalizar compra: {str(e)}', 'danger')
        return redirect(url_for('ver_carrinho'))
    

@app.route('/buscar', methods=['GET'])
def buscar_produtos():
    # Obtém o termo de busca da URL (/?q=termo)
    termo_busca = request.args.get('q', '').strip()
    
    # Se não houver termo de busca, redireciona para a página inicial
    if not termo_busca:
        return redirect(url_for('home'))
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        # Busca produtos onde o nome OU descrição contém o termo (case insensitive)
        cursor.execute('''
            SELECT * FROM produtos 
            WHERE LOWER(nome) LIKE LOWER(?) OR LOWER(descricao) LIKE LOWER(?)
            ORDER BY nome
        ''', (f'%{termo_busca}%', f'%{termo_busca}%'))
        
        produtos = cursor.fetchall()
        
        # Se não encontrar produtos, mostra mensagem
        if not produtos:
            flash(f'Nenhum produto encontrado para "{termo_busca}"', 'info')
            return redirect(url_for('home'))
            
    except Exception as e:
        flash(f'Erro ao buscar produtos: {str(e)}', 'danger')
        return redirect(url_for('home'))
        
    finally:
        conn.close()
    
    return render_template('index.html', produtos=produtos, termo_busca=termo_busca)

@app.route('/historico-pedidos')
def historico_pedidos():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado', 'warning')
        return redirect(url_for('login'))
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Buscar pedidos do usuário
    cursor.execute('''
        SELECT id, data, status, total
        FROM pedidos
        WHERE usuario_id = ?
        ORDER BY data DESC
    ''', (session['usuario_id'],))
    
    pedidos = cursor.fetchall()
    
    historico = []
    for pedido in pedidos:
        # Buscar itens do pedido - observe os índices
        cursor.execute('''
            SELECT pi.quantidade, pi.preco_unitario, pr.nome
            FROM pedido_itens pi
            JOIN produtos pr ON pi.produto_id = pr.id
            WHERE pi.pedido_id = ?
        ''', (pedido[0],))
        
        itens = []
        for item in cursor.fetchall():
            itens.append({
                'quantidade': item[0],       # índice 0 = quantidade
                'preco_unitario': item[1],   # índice 1 = preco_unitario
                'nome': item[2]              # índice 2 = nome
            })
        
        historico.append({
            'id': pedido[0],
            'data': pedido[1],
            'status': pedido[2],
            'total': pedido[3],
            'itens': itens
        })
    
    conn.close()
    return render_template('historico_pedidos.html', historico=historico)

@app.route('/confirmacao-pedido/<int:pedido_id>')
def confirmacao_pedido(pedido_id):
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para ver esta página', 'warning')
        return redirect(url_for('login'))
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Buscar informações do pedido
    cursor.execute('''
        SELECT id, data, status, total
        FROM pedidos
        WHERE id = ? AND usuario_id = ?
    ''', (pedido_id, session['usuario_id']))
    
    pedido = cursor.fetchone()
    
    if not pedido:
        flash('Pedido não encontrado', 'danger')
        return redirect(url_for('home'))
    
    # Buscar itens do pedido
    cursor.execute('''
        SELECT pi.quantidade, pi.preco_unitario, pr.nome
        FROM pedido_itens pi
        JOIN produtos pr ON pi.produto_id = pr.id
        WHERE pi.pedido_id = ?
    ''', (pedido_id,))
    
    itens = cursor.fetchall()
    conn.close()
    
    return render_template('confirmacao_pedido.html',
                         pedido={
                             'id': pedido[0],
                             'data': pedido[1],
                             'status': pedido[2],
                             'total': pedido[3],
                             'itens': itens
                         })

if __name__ == '__main__':
    inicializar_banco()
    app.run(debug=True, port=5001)
