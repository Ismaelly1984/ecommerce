from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from werkzeug.utils import secure_filename
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

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
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
  
    # Criar tabela de usuários (apenas uma vez)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

    # Verificar se já existe um admin
    cursor.execute('SELECT COUNT(*) FROM usuarios WHERE is_admin = 1')
    if cursor.fetchone()[0] == 0:
        # Adicionar usuário admin padrão se não existir
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('Admin', 'admin@example.com', generate_password_hash('admin123'), 1))
        conn.commit()

    # Restante das tabelas...
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
    # Criar tabela de produtos se não existir
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
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
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

    cursor.execute('SELECT COUNT(*) FROM produtos')
    if cursor.fetchone()[0] == 0:
        # Produtos básicos iniciais
        cursor.execute("""
            INSERT INTO produtos (nome, preco, estoque, descricao, imagem) 
            VALUES ('Camiseta Básica', 49.90, 100, 'Camiseta 100% algodão, disponível em várias cores', 'camiseta.jpg')
        """)
        
        cursor.execute("""
            INSERT INTO produtos (nome, preco, estoque, descricao, imagem) 
            VALUES ('Calça Jeans Slim', 129.90, 50, 'Calça jeans masculina modelo slim fit', 'calca_jeans.jpg')
        """)

        # Lista de produtos adicionais com descrições e imagens
        produtos = [
            {
                "nome": "Tênis Esportivo",
                "preco": 199.90,
                "estoque": 60,
                "descricao": "Tênis para corrida com amortecimento premium",
                "imagem": "tenis.jpg"
            },
            {
                "nome": "Jaqueta Corta-Vento",
                "preco": 149.90,
                "estoque": 40,
                "descricao": "Jaqueta impermeável para atividades ao ar livre",
                "imagem": "jaqueta.jpg"
            },
            {
                "nome": "Boné Estilizado",
                "preco": 39.90,
                "estoque": 80,
                "descricao": "Boné ajustável com design moderno",
                "imagem": "bone.jpg"
            },
            {
                "nome": "Mochila Escolar",
                "preco": 89.90,
                "estoque": 30,
                "descricao": "Mochila resistente com compartimento para notebook",
                "imagem": "mochila.jpg"
            },
            {
                "nome": "Relógio Digital",
                "preco": 129.90,
                "estoque": 25,
                "descricao": "Relógio inteligente com monitor cardíaco",
                "imagem": "relogio.jpg"
            },
            {
                "nome": "Óculos de Sol",
                "preco": 59.90,
                "estoque": 70,
                "descricao": "Óculos com proteção UV 400 e armação leve",
                "imagem": "oculos.jpg"
            },
            {
                "nome": "Vestido Floral",
                "preco": 99.90,
                "estoque": 45,
                "descricao": "Vestido leve para verão com estampa floral",
                "imagem": "vestido.jpg"
            },
            {
                "nome": "Sandália Feminina",
                "preco": 79.90,
                "estoque": 55,
                "descricao": "Sandália confortável com salto baixo",
                "imagem": "sandalia.jpg"
            },
            {
                "nome": "Camisa Polo",
                "preco": 69.90,
                "estoque": 90,
                "descricao": "Camisa polo em algodão piquet",
                "imagem": "polo.jpg"
            },
            {
                "nome": "Blusa de Moletom",
                "preco": 119.90,
                "estoque": 35,
                "descricao": "Blusa de moletom com capuz e bolso",
                "imagem": "moletom.jpg"
            }
        ]

        # Inserção dos produtos adicionais
        for produto in produtos:
            cursor.execute("""
                INSERT INTO produtos (nome, preco, estoque, descricao, imagem)
                VALUES (?, ?, ?, ?, ?)
            """, (produto["nome"], produto["preco"], produto["estoque"], produto["descricao"], produto["imagem"]))

        conn.commit()
        print("Banco de dados populado com produtos iniciais!")

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
    pagina = request.args.get('pagina', 1, type=int)
    produtos_por_pagina = 10
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Calcular offset
    offset = (pagina - 1) * produtos_por_pagina
    
    # Buscar produtos com limite e offset
    cursor.execute('''
        SELECT * FROM produtos
        LIMIT ? OFFSET ?
    ''', (produtos_por_pagina, offset))
    
    produtos = cursor.fetchall()
    
    # Verificar se há mais produtos
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
    
    # Verificar se há mais produtos
    cursor.execute('SELECT COUNT(*) FROM produtos')
    total_produtos = cursor.fetchone()[0]
    tem_mais = (offset + produtos_por_pagina) < total_produtos
    
    conn.close()
    
    # Renderizar apenas os produtos como HTML
    produtos_html = render_template('index.html', produtos=produtos)
    
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
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, nome, senha, is_admin FROM usuarios WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['senha'], senha):
            session['usuario_id'] = user['id']
            session['usuario_nome'] = user['nome']
            session['is_admin'] = bool(user['is_admin'])
            
            # Registrar log de login
            cursor.execute('''
                INSERT INTO logs_atividades (usuario_id, acao)
                VALUES (?, ?)
            ''', (user['id'], 'login'))
            
            conn.commit()
            conn.close()
          
            # Redirecionar admin para o dashboard
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))

        conn.close()
        flash('Usuário ou senha incorretos', 'danger')
    
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
    
    carrinho = session.get('carrinho', [])
    if not carrinho:
        flash('Seu carrinho está vazio', 'danger')
        return redirect(url_for('ver_carrinho'))
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Calcular total do carrinho
        total = sum(item['preco'] * item['quantidade'] for item in carrinho)
        
        # 1. Criar o pedido no banco de dados
        cursor.execute('''
            INSERT INTO pedidos (usuario_id, data, status, total)
            VALUES (?, datetime('now'), 'Processando', ?)
        ''', (session['usuario_id'], total))
        
        pedido_id = cursor.lastrowid
        
        # 2. Inserir cada item comprado na tabela pedido_itens
        for item in carrinho:
            produto_id = item['produto_id']
            quantidade = item['quantidade']
            preco_unitario = item['preco']
            
            # Inserir item no pedido_itens
            cursor.execute('''
                INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
            ''', (pedido_id, produto_id, quantidade, preco_unitario))
            
            # 3. Atualizar estoque do produto
            cursor.execute('''
                UPDATE produtos
                SET estoque = estoque - ?
                WHERE id = ? AND estoque >= ?
            ''', (quantidade, produto_id, quantidade))
            
            cursor.execute('''
                 INSERT INTO logs_atividades (usuario_id, acao, detalhes)
                  VALUES (?, ?, ?)
                    ''', (session['usuario_id'], 'finalizou compra', f'Pedido ID: {pedido_id}, Total: {total}'))
   
            if cursor.rowcount == 0:
                # Estoque insuficiente, abortar compra
                conn.rollback()
                flash(f'Estoque insuficiente para o produto {item["nome"]}.', 'danger')
                return redirect(url_for('ver_carrinho'))
        
        # 4. Confirmar as alterações no banco e limpar carrinho
        conn.commit()
        session.pop('carrinho', None)
        
        flash('Compra finalizada com sucesso!', 'success')
        return redirect(url_for('home'))
    
    except Exception as e:
        conn.rollback()
        flash('Erro ao finalizar a compra. Tente novamente.', 'danger')
        print(f"Erro ao finalizar compra: {e}")
        return redirect(url_for('ver_carrinho'))
    
    finally:
        conn.close()

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

# Decorator para verificar se o usuário é admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se o usuário está logado e é admin
        # Você precisará adicionar uma coluna 'is_admin' na tabela de usuários
        if 'usuario_id' not in session or not session.get('is_admin', False):
            flash('Acesso restrito a administradores', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/admin/produtos')
@admin_required
def admin_produtos():
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM produtos ORDER BY nome')
    produtos = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/produtos.html', produtos=produtos)

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
        
        cursor.execute('''
            UPDATE produtos 
            SET nome=?, preco=?, estoque=?, descricao=?
            WHERE id=?
        ''', (nome, preco, estoque, descricao, id))
        
        conn.commit()
        conn.close()
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_produtos'))
    
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
    
    cursor.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Produto excluído com sucesso!', 'success')
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
    
    # Informações do pedido
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
    
    # Itens do pedido
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
    
    cursor.execute('''
        UPDATE pedidos
        SET status = ?
        WHERE id = ?
    ''', (novo_status, id))
    
    conn.commit()
    conn.close()
    
    flash('Status do pedido atualizado com sucesso!', 'success')
    return redirect(url_for('detalhes_pedido', id=id))

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, nome, email FROM usuarios ORDER BY nome')
    usuarios = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/usuarios.html', usuarios=usuarios)

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

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = conectar_db()
    conn.row_factory = sqlite3.Row  # Para retornar dicionários
    cursor = conn.cursor()
    
    # Estatísticas principais
    stats = {
        'total_produtos': cursor.execute('SELECT COUNT(*) FROM produtos').fetchone()[0],
        'total_usuarios': cursor.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0],
        'total_pedidos': cursor.execute('SELECT COUNT(*) FROM pedidos').fetchone()[0],
        'vendas_totais': cursor.execute('SELECT SUM(total) FROM pedidos WHERE status = "Entregue"').fetchone()[0] or 0
    }
    
    # Últimos pedidos (5 mais recentes)
    ultimos_pedidos = cursor.execute('''
        SELECT p.id, p.data, p.status, p.total, u.nome 
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.data DESC
        LIMIT 5
    ''').fetchall()
    
    # Produtos com estoque baixo
    produtos_estoque_baixo = cursor.execute('''
        SELECT id, nome, estoque 
        FROM produtos 
        WHERE estoque < 10 
        ORDER BY estoque ASC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         ultimos_pedidos=ultimos_pedidos,
                         produtos_estoque_baixo=produtos_estoque_baixo)

@app.route('/admin/produtos/novo', methods=['GET', 'POST'])
@admin_required
def novo_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])
        descricao = request.form['descricao']
        
        # Processar upload de imagem
        imagem = None
        if 'imagem' in request.files:
            arquivo = request.files['imagem']
            if arquivo.filename != '':
                if arquivo and allowed_file(arquivo.filename):
                    filename = secure_filename(arquivo.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    arquivo.save(filepath)
                    imagem = filename
        
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO produtos (nome, preco, estoque, descricao, imagem)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, preco, estoque, descricao, imagem))
        
        conn.commit()
        conn.close()
        
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('admin_produtos'))
    
    return render_template('admin/novo_produto.html')

if __name__ == '__main__':
    inicializar_banco()
    app.run(debug=True, port=5001)
