import sqlite3
import os
from werkzeug.security import generate_password_hash
from config import Config # Importar Config

DB_NAME = Config.DB_NAME # Usar o nome do DB de config

def conectar_db():
    """
    Conecta ao banco de dados SQLite.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome (como dicionário)
    return conn

def inserir_produtos_iniciais():
    """
    Insere uma lista de produtos iniciais no banco de dados,
    verificando se já existem para evitar duplicatas.
    """
    produtos = [
        {
            "nome": "Mocassim Masculino Casual em Couro Azul Estampado",
            "preco": 189.90,
            "estoque": 50,
            "descricao": "Mocassim masculino casual confeccionado em couro sintético com textura que imita pele de crocodilo em tom azul. Possui detalhe de tira com fivela metálica prateada sobre o cabedal. Solado emborrachado antiderrapante e costura aparente. Ideal para um look moderno e confortável.",
            "imagem": "pexels-pixabay-267301.jpg" # Nome do arquivo local
        },
        {
            "nome": "Mocassim Masculino Casual em Couro Laranja Texturizado",
            "preco": 179.90,
            "estoque": 45,
            "descricao": "Mocassim masculino em couro sintético texturizado na cor laranja. Apresenta detalhe de tira com fivela metálica prateada. Interior confortável e solado flexível para o dia a dia.",
            "imagem": "pexels-jose-martin-segura-benites-1422456152-27609337.jpg" # Nome do arquivo local
        },
        {
            "nome": "Mocassim Masculino Clássico em Camurça Cinza",
            "preco": 199.90,
            "estoque": 60,
            "descricao": "Mocassim masculino de estilo clássico confeccionado em camurça na cor cinza. Possui um design minimalista com detalhe de tira e fivela metálica prateada. Perfeito para ocasiões que pedem um toque de elegância discreta.",
            "imagem": "pexels-jose-martin-segura-benites-1422456152-27381284.jpg" # Nome do arquivo local
        },
        {
            "nome": "Mocassim Feminino Elegante em Couro Caramelo Texturizado",
            "preco": 210.50,
            "estoque": 40,
            "descricao": "Mocassim feminino elegante em couro sintético com textura croco na cor caramelo. Detalhe de tira com adorno metálico prateado sobre o peito do pé. Salto baixo discreto e solado confortável. Ideal para looks de trabalho ou passeios.",
            "imagem": "pexels-maryiaplashchynskaya-3615455.jpg" # Nome do arquivo local
        },
        {
            "nome": "Mocassim Feminino Moderno em Couro Marrom Médio Texturizado",
            "preco": 205.00,
            "estoque": 35,
            "descricao": "Mocassim feminino moderno em couro sintético com padrão texturizado em tom marrom médio. Possui detalhe de tira com fivela geométrica prateada. Design versátil que combina com diversas ocasiões.",
            "imagem": "pexels-pixabay-267301.jpg" # Nome do arquivo local (reutilizando, se for o caso)
        },
        {
            "nome": "Mocassim Feminino Sofisticado em Couro Marrom Escuro Texturizado",
            "preco": 220.00,
            "estoque": 30,
            "descricao": "Mocassim feminino sofisticado em couro sintético com acabamento texturizado em marrom escuro. Apresenta tira com fivela metálica prateada, conferindo um toque de elegância. Confortável para uso prolongado.",
            "imagem": "pexels-jose-martin-segura-benites-1422456152-27658532.jpg" # Nome do arquivo local
        },
        {
            "nome": "Bota Feminina Cano Curto em Couro Marrom com Salto Bloco",
            "preco": 320.00,
            "estoque": 25,
            "descricao": "Bota feminina de cano curto confeccionada em couro sintético marrom. Possui salto bloco de altura média e solado tratorado para maior aderência. Design moderno e confortável para diversas ocasiões.",
            "imagem": "pexels-jose-martin-segura-benites-1422456152-27658532 (1).jpg" # Nome do arquivo local
        },
        {
            "nome": "Bota Feminina Cano Curto em Couro Marrom com Detalhe em Camurça e Zíper",
            "preco": 350.00,
            "estoque": 20,
            "descricao": "Bota feminina de cano curto em couro sintético marrom com detalhe em camurça na parte superior do cano. Possui zíper lateral para facilitar o calce e salto alto robusto.",
            "imagem": "pexels-antonio-bracho-421912472-19113849.jpg" # Nome do arquivo local
        },
        {
            "nome": "Bota Coturno Feminina em Verniz Preto com Cadarço e Solado Tratorado",
            "preco": 280.00,
            "estoque": 30,
            "descricao": "Bota estilo coturno feminina em verniz preto brilhante. Possui fechamento em cadarço frontal, ilhós metálicos e solado tratorado robusto. Ideal para um visual moderno e cheio de atitude.",
            "imagem": "pexels-jose-martin-segura-benites-1422456152-27256455.jpg" # Nome do arquivo local
        },
        {
            "nome": "Bota Coturno Feminina em Couro Sintético Bordô com Cadarço",
            "preco": 295.00,
            "estoque": 28,
            "descricao": "Bota estilo coturno feminina em couro sintético na cor bordô com detalhes de costura contrastante. Fechamento em cadarço frontal e solado antiderrapante.",
            "imagem": "pexels-jose-martin-segura-benites-1422456152-27352801.jpg" # Nome do arquivo local
        },
        {
            "nome": "Bota Feminina Cano Curto em Couro Marrom com Salto Bloco e Fivela",
            "preco": 310.00,
            "estoque": 22,
            "descricao": "Bota feminina de cano curto em couro sintético marrom com detalhe de tira e fivela lateral metálica. Possui salto bloco de altura confortável e zíper lateral para facilitar o calce.",
            "imagem": "pexels-jose-martin-segura-benites-1422456152-27352801.jpg" # Nome do arquivo local (reutilizando uma imagem similar)
        }
    ]

    conn = conectar_db()
    cursor = conn.cursor()

    for produto in produtos:
        try:
            # Verifica se o produto já existe pelo nome antes de inserir
            cursor.execute('SELECT id FROM produtos WHERE nome = ?', (produto['nome'],))
            if cursor.fetchone() is None:
                cursor.execute('''
                    INSERT INTO produtos (nome, preco, estoque, descricao, imagem)
                    VALUES (?, ?, ?, ?, ?)
                ''', (produto['nome'], produto['preco'], produto['estoque'], produto['descricao'], produto['imagem']))
                print(f"Produto '{produto['nome']}' inserido com sucesso.")
            else:
                print(f"Produto '{produto['nome']}' já existe. Ignorando inserção.")
        except sqlite3.IntegrityError:
            # Em caso de erro de integridade (ex: nome UNIQUE)
            print(f"Erro de integridade ao inserir o produto '{produto['nome']}'. Pode ser um problema de chave única.")
        except Exception as e:
            print(f"Erro geral ao inserir o produto '{produto['nome']}': {e}")

    conn.commit()
    conn.close()

def inicializar_banco():
    """
    Inicializa o banco de dados, criando as tabelas necessárias
    e adicionando um usuário administrador padrão se não existir.
    Após criar as tabelas, insere os produtos iniciais.
    """
    conn = conectar_db()
    cursor = conn.cursor()

    # Criação da tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

    # Criação da tabela de produtos
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

    # Criação da tabela de carrinho
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carrinho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 1,
            data_adicionado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE,
            UNIQUE(usuario_id, produto_id) -- Garante que um usuário só tenha um item de um produto no carrinho
        )
    ''')

    # Criação da tabela de pedidos
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

    # Criação da tabela de itens do pedido
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

    # Criação da tabela de logs de atividades
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
        print("Usuário Admin padrão criado.")

    conn.close()

    # Chama a função para inserir os produtos iniciais após as tabelas serem criadas
    inserir_produtos_iniciais()


def contar_itens_carrinho_db(usuario_id):
    """
    Conta o número total de itens (quantidade somada) no carrinho de um usuário.
    """
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
    """
    Adiciona um produto ao carrinho ou atualiza sua quantidade se já existir.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Verifica se o produto já está no carrinho do usuário
    cursor.execute('SELECT quantidade FROM carrinho WHERE usuario_id = ? AND produto_id = ?', (usuario_id, produto_id))
    item_existente = cursor.fetchone()

    if item_existente:
        # Se o item já existe, atualiza a quantidade
        nova_quantidade = item_existente['quantidade'] + quantidade
        cursor.execute('''
            UPDATE carrinho
            SET quantidade = ?
            WHERE usuario_id = ? AND produto_id = ?
        ''', (nova_quantidade, usuario_id, produto_id))
    else:
        # Se o item não existe, insere-o no carrinho
        cursor.execute('''
            INSERT INTO carrinho (usuario_id, produto_id, quantidade)
            VALUES (?, ?, ?)
        ''', (usuario_id, produto_id, quantidade))
    
    conn.commit()
    conn.close()

def remover_do_carrinho_db(usuario_id, produto_id):
    """
    Remove um produto específico do carrinho de um usuário.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM carrinho
    WHERE usuario_id = ? AND produto_id = ?
    ''', (usuario_id, produto_id))
    conn.commit()
    conn.close()

def atualizar_quantidade_carrinho_db(usuario_id, produto_id, nova_quantidade):
    """
    Atualiza a quantidade de um item no carrinho de um usuário.
    Se a nova_quantidade for 0 ou menos, remove o item do carrinho.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    if nova_quantidade <= 0:
        cursor.execute('''
            DELETE FROM carrinho
            WHERE usuario_id = ? AND produto_id = ?
        ''', (usuario_id, produto_id))
    else:
        cursor.execute('''
            UPDATE carrinho
            SET quantidade = ?
            WHERE usuario_id = ? AND produto_id = ?
        ''', (nova_quantidade, usuario_id, produto_id))
    conn.commit()
    conn.close()

def calcular_total_carrinho_db(usuario_id):
    """
    Calcula o valor total do carrinho e o número total de itens (quantidade somada)
    para um usuário específico.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.preco, c.quantidade
        FROM carrinho c
        JOIN produtos p ON c.produto_id = p.id
        WHERE c.usuario_id = ?
    ''', (usuario_id,))
    itens = cursor.fetchall()
    conn.close()

    total_carrinho = sum(item['preco'] * item['quantidade'] for item in itens)
    total_itens_no_carrinho = sum(item['quantidade'] for item in itens)
    return total_carrinho, total_itens_no_carrinho

def get_produto_por_id(produto_id):
    """
    Obtém os detalhes de um produto pelo seu ID.
    Inclui o estoque na consulta.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, preco, imagem, estoque, descricao FROM produtos WHERE id = ?', (produto_id,)) # Incluído 'descricao' e 'estoque'
    produto = cursor.fetchone()
    conn.close()
    return produto

def registrar_log(usuario_id, acao, detalhes=None):
    """
    Registra uma ação do usuário no banco de dados de logs.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs_atividades (usuario_id, acao, detalhes)
        VALUES (?, ?, ?)
    ''', (usuario_id, acao, detalhes))
    conn.commit()
    conn.close()