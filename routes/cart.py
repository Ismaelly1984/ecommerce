from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import conectar_db, adicionar_ao_carrinho_db, remover_do_carrinho_db, get_produto_por_id
from utils.decorators import login_required

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/adicionar_ao_carrinho/<int:produto_id>', methods=['POST'])
@login_required
def adicionar_ao_carrinho(produto_id):
    try:
        produto_info = get_produto_por_id(produto_id)

        if not produto_info:
            flash('Produto não encontrado.', 'danger')
            return redirect(request.referrer or url_for('main.home'))

        if produto_info['estoque'] < 1:
            flash(f'Produto "{produto_info["nome"]}" está fora de estoque.', 'danger')
            return redirect(request.referrer or url_for('main.home'))

        adicionar_ao_carrinho_db(session['usuario_id'], produto_id, 1)
        flash('Produto adicionado ao carrinho!', 'success')
    except Exception as e:
        flash(f'Erro ao adicionar produto ao carrinho: {e}', 'danger')
        print(f"Error adding to cart: {e}")
    return redirect(request.referrer or url_for('main.home'))

@cart_bp.route('/remover_do_carrinho/<int:produto_id>', methods=['POST'])
@login_required
def remover_do_carrinho(produto_id):
    try:
        remover_do_carrinho_db(session['usuario_id'], produto_id)
        flash('Produto removido do carrinho.', 'info')
    except Exception as e:
        flash(f'Erro ao remover produto do carrinho: {e}', 'danger')
        print(f"Error removing from cart: {e}")
    return redirect(url_for('cart.ver_carrinho'))

@cart_bp.route('/carrinho')
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

    itens = cursor.fetchall()
    conn.close()

    total = sum(item['preco'] * item['quantidade'] for item in itens)
    return render_template('carrinho.html', carrinho=itens, total=total)