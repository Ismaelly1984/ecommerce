import sqlite3
import os
from werkzeug.security import generate_password_hash
from config import Config # Importar Config

DB_NAME = Config.DB_NAME # Usar o nome do DB de config

def conectar_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return conn

def inicializar_banco():
    conn = conectar_db()
    cursor = conn.cursor()

    # Criação das tabelas
    # O código de criação das tabelas continua o mesmo, mas agora está aqui.
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

    # Adicionar usuário admin se não existir
    cursor.execute('SELECT COUNT(*) FROM usuarios WHERE is_admin = 1')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('Admin', 'admin@example.com', generate_password_hash('admin123'), 1))
        conn.commit()
        print("Admin user created.")

    conn.close()

# Funções de operação do carrinho no DB (apenas para acesso interno, não rotas)
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

# Exemplo de função para obter detalhes do produto (poderia ir para models.py)
def get_produto_por_id(produto_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,))
    produto = cursor.fetchone()
    conn.close()
    return produto

# Exemplo de função para registrar log
def registrar_log(usuario_id, acao, detalhes=None):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs_atividades (usuario_id, acao, detalhes)
        VALUES (?, ?, ?)
    ''', (usuario_id, acao, detalhes))
    conn.commit()
    conn.close()