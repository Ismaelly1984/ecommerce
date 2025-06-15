from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import (
    conectar_db,
    adicionar_ao_carrinho_db,
    remover_do_carrinho_db,
    get_produto_por_id,
    atualizar_quantidade_carrinho_db,
    calcular_total_carrinho_db
)
from utils.decorators import login_required

# Defina o blueprint UMA ÚNICA VEZ
cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/adicionar_ao_carrinho/<int:produto_id>', methods=['POST'])
@login_required
def adicionar_ao_carrinho(produto_id):
    """
    Adiciona um produto ao carrinho do usuário.
    Realiza validação de estoque antes da adição.
    """
    try:
        produto_info = get_produto_por_id(produto_id)

        if not produto_info:
            flash('Produto não encontrado.', 'danger')
            return redirect(request.referrer or url_for('main.home'))

        # Quantidade que o usuário deseja adicionar (padrão é 1 se não especificado)
        quantidade_a_adicionar = int(request.form.get('quantidade', 1))

        if quantidade_a_adicionar <= 0:
            flash('A quantidade a adicionar deve ser maior que zero.', 'danger')
            return redirect(request.referrer or url_for('main.home'))

        conn = conectar_db()
        cursor = conn.cursor()
        
        # Pega a quantidade atual do produto no carrinho do usuário
        cursor.execute('SELECT quantidade FROM carrinho WHERE usuario_id = ? AND produto_id = ?', 
                       (session['usuario_id'], produto_id))
        item_no_carrinho = cursor.fetchone()
        conn.close()

        quantidade_ja_no_carrinho = item_no_carrinho['quantidade'] if item_no_carrinho else 0
        nova_quantidade_total = quantidade_ja_no_carrinho + quantidade_a_adicionar

        # Validação de estoque: verifica se a nova quantidade total excede o estoque disponível
        if nova_quantidade_total > produto_info['estoque']:
            flash(f'Não há estoque suficiente para adicionar {quantidade_a_adicionar} unidades de "{produto_info["nome"]}". Disponível: {produto_info["estoque"] - quantidade_ja_no_carrinho} para adição.', 'warning')
            return redirect(request.referrer or url_for('main.home'))
        
        if produto_info['estoque'] == 0:
             flash(f'Produto "{produto_info["nome"]}" está fora de estoque.', 'danger')
             return redirect(request.referrer or url_for('main.home'))


        adicionar_ao_carrinho_db(session['usuario_id'], produto_id, quantidade_a_adicionar)
        flash(f'{quantidade_a_adicionar} unidade(s) de "{produto_info["nome"]}" adicionada(s) ao carrinho!', 'success')

    except Exception as e:
        flash(f'Erro ao adicionar produto ao carrinho: {e}', 'danger')
        print(f"Error adding to cart: {e}")
    return redirect(request.referrer or url_for('main.home'))

# Rota para remover item do carrinho via AJAX (e fallback para requisições não-AJAX)
@cart_bp.route('/remover_do_carrinho/<int:produto_id>', methods=['POST'])
@login_required
def remover_do_carrinho(produto_id):
    """
    Remove um produto específico do carrinho de um usuário.
    Suporta remoção via AJAX (retornando JSON) ou via formulário HTML (redirecionando).
    """
    try:
        remover_do_carrinho_db(session['usuario_id'], produto_id)

        # Após remover, recalcula o total do carrinho e número de itens do DB
        cart_total, total_itens = calcular_total_carrinho_db(session['usuario_id'])

        if request.is_json: # Se a requisição veio via AJAX (do JS)
            return jsonify({
                'message': 'Item removido com sucesso!',
                'cart_total': cart_total,
                'total_itens': total_itens,
                'type': 'success',
                'produto_id': produto_id # Retorna o ID para o frontend remover o elemento
            }), 200
        else: # Se a requisição veio via formulário HTML normal (fallback)
            flash('Produto removido do carrinho.', 'info')
            return redirect(url_for('cart.ver_carrinho'))

    except Exception as e:
        print(f"Erro ao remover produto do carrinho: {e}")
        if request.is_json:
            return jsonify({'message': f'Erro ao remover produto: {e}', 'type': 'error'}), 500
        else:
            flash(f'Erro ao remover produto do carrinho: {e}', 'danger')
            return redirect(url_for('cart.ver_carrinho'))


@cart_bp.route('/carrinho')
@login_required
def ver_carrinho():
    """
    Exibe o conteúdo do carrinho de compras do usuário.
    """
    conn = conectar_db()
    cursor = conn.cursor()

    # Seleciona informações do produto e a quantidade do carrinho
    cursor.execute('''
    SELECT p.id, p.nome, p.preco, c.quantidade, p.imagem, p.estoque
    FROM carrinho c
    JOIN produtos p ON c.produto_id = p.id
    WHERE c.usuario_id = ?
    ORDER BY c.data_adicionado DESC -- Ordena para manter a ordem consistente
    ''', (session['usuario_id'],))

    itens = cursor.fetchall() # Isso retornará uma lista de objetos Row (como dicionários)
    conn.close()

    total_carrinho = sum(item['preco'] * item['quantidade'] for item in itens)
    total_itens_no_carrinho = sum(item['quantidade'] for item in itens)

    return render_template('carrinho.html', carrinho=itens, total=total_carrinho, total_itens=total_itens_no_carrinho)


# Rota para atualizar a quantidade de um item no carrinho via AJAX
@cart_bp.route('/atualizar_quantidade', methods=['POST'])
@login_required # Garante que o usuário esteja logado
def atualizar_quantidade_carrinho():
    """
    Atualiza a quantidade de um item específico no carrinho do usuário.
    Recebe dados via JSON e retorna uma resposta JSON.
    """
    data = request.get_json() # Pega os dados JSON da requisição
    product_id = data.get('product_id')
    quantidade = data.get('quantidade')

    # Validação de entrada
    if not product_id or not isinstance(quantidade, int) or quantidade < 0: # Quantidade pode ser 0 para remover
        return jsonify({'message': 'Dados de quantidade inválidos.', 'type': 'error'}), 400

    try:
        # 1. Obter informações do produto, incluindo estoque
        produto_info = get_produto_por_id(product_id)
        if not produto_info:
            return jsonify({'message': 'Produto não encontrado.', 'type': 'error'}), 404

        # 2. Validar estoque (apenas se a quantidade for maior que 0)
        if quantidade > 0 and quantidade > produto_info['estoque']:
            return jsonify({
                'message': f'Quantidade em estoque insuficiente para "{produto_info["nome"]}". Disponível: {produto_info["estoque"]}.',
                'type': 'error',
                'current_stock': produto_info['estoque'] # Retornar o estoque atual para o frontend
            }), 400

        # 3. Atualizar a quantidade no banco de dados
        # A função `atualizar_quantidade_carrinho_db` já lida com a remoção se quantidade for <= 0
        atualizar_quantidade_carrinho_db(session['usuario_id'], product_id, quantidade)

        # 4. Recalcular o subtotal do item (se o item ainda estiver no carrinho)
        item_subtotal = 0.0
        if quantidade > 0: # Se o item não foi removido
            item_subtotal = produto_info['preco'] * quantidade

        # 5. Recalcular o total geral do carrinho e o número total de itens do DB
        cart_total, total_itens = calcular_total_carrinho_db(session['usuario_id'])

        return jsonify({
            'message': 'Quantidade atualizada com sucesso!',
            'item_subtotal': item_subtotal, # Pode ser 0 se o item foi removido
            'cart_total': cart_total,
            'total_itens': total_itens,
            'type': 'success'
        }), 200

    except Exception as e:
        print(f"Erro ao atualizar quantidade no carrinho: {e}")
        return jsonify({'message': f'Erro interno ao atualizar quantidade: {e}', 'type': 'error'}), 500

