from flask import Blueprint, render_template, request, abort, jsonify, url_for, redirect, flash, Response
from database import conectar_db, get_produto_por_id
from utils.helpers import formatar_moeda # Se precisar usar formatar_moeda no HTML
import io # Manter importação de io se precisar de outras operações com bytes

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
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

@main_bp.route('/produto/<int:id>')
def detalhes_produto(id):
    produto = get_produto_por_id(id) # Usar função do database.py

    if produto is None:
        abort(404)

    # Converter para dict se necessário para template, mas row_factory já faz isso
    produto_dict = dict(produto) # Converter Row para dict explícito se preferir

    return render_template('detalhes_produto.html', produto=produto_dict)

@main_bp.route('/carregar-mais-produtos')
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

    # Assumindo que você tem um partial template para os cards
    produtos_html = render_template('partials/product_cards.html', produtos=produtos)

    return jsonify({
        'html': produtos_html,
        'tem_mais': tem_mais,
        'proxima_pagina': pagina + 1
    })

@main_bp.route('/buscar', methods=['GET'])
def buscar_produtos():
    termo_busca = request.args.get('q', '').strip()
    pagina = request.args.get('pagina', 1, type=int) # Para busca paginada
    produtos_por_pagina = 10
    offset = (pagina - 1) * produtos_por_pagina

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        if not termo_busca:
            # Se não há termo de busca, lista todos os produtos como na home
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

        # Se há termo de busca, realiza a busca
        cursor.execute('''
            SELECT * FROM produtos
            WHERE LOWER(nome) LIKE LOWER(?) OR LOWER(descricao) LIKE LOWER(?)
            ORDER BY nome
        ''', (f'%{termo_busca}%', f'%{termo_busca}%'))

        produtos = cursor.fetchall()
        tem_mais = False # Busca não é paginada, então não tem "mais" aqui

        if not produtos:
            flash(f'Nenhum produto encontrado para "{termo_busca}"', 'info')
            return render_template('index.html', produtos=[], termo_busca=termo_busca)

    except Exception as e:
        flash(f'Erro ao buscar produtos: {str(e)}', 'danger')
        return redirect(url_for('main.home'))

    finally:
        conn.close()

    # Para resultados de busca específicos, não há paginação 'tem_mais' aqui.
    # Se quiser paginação na busca, a lógica seria mais complexa.
    return render_template('index.html', produtos=produtos, termo_busca=termo_busca, tem_mais=False)

@main_bp.route('/contato')
def contato():
    """
    Exibe a página do formulário de contato.
    """
    return render_template('contato.html')

@main_bp.route('/enviar_contato', methods=['POST'])
def enviar_contato():
    """
    Processa o envio do formulário de contato.
    Esta rota só aceita requisições POST.
    """
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        mensagem = request.form.get('mensagem')

        if not nome or not email or not mensagem:
            flash('Por favor, preencha todos os campos do formulário.', 'danger')
            return redirect(url_for('main.contato'))
        
        print(f"DEBUG: Formulário de Contato Recebido:")
        print(f"  Nome: {nome}")
        print(f"  Email: {email}")
        print(f"  Mensagem: {mensagem}")

        flash('Sua mensagem foi enviada com sucesso! Em breve entraremos em contato.', 'success')
        return redirect(url_for('main.contato'))
    
    return redirect(url_for('main.contato'))

@main_bp.route('/sobre')
def sobre():
    return render_template('sobre.html')