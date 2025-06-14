from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import conectar_db, registrar_log
from utils.decorators import login_required
import datetime # Importar datetime aqui

checkout_bp = Blueprint('checkout', __name__)

@checkout_bp.route('/finalizar-compra', methods=['POST'])
@login_required
def finalizar_compra():
    conn = conectar_db()
    cursor = conn.cursor()

    try:
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
            return redirect(url_for('cart.ver_carrinho'))

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
                return redirect(url_for('cart.ver_carrinho'))

            cursor.execute('''
                INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
            ''', (pedido_id, produto_id, quantidade_no_carrinho, preco_unitario))

            cursor.execute('''
                UPDATE produtos
                SET estoque = estoque - ?
                WHERE id = ?
            ''', (quantidade_no_carrinho, produto_id))

        registrar_log(session['usuario_id'], 'finalizou compra', f'Pedido ID: {pedido_id}, Total: {total}')

        # 3. Clear the user's cart in the database
        cursor.execute('DELETE FROM carrinho WHERE usuario_id = ?', (session['usuario_id'],))

        conn.commit()
        flash('Compra finalizada com sucesso!', 'success')
        return redirect(url_for('checkout.confirmacao_pedido', pedido_id=pedido_id))

    except Exception as e:
        conn.rollback()
        flash('Erro ao finalizar a compra. Tente novamente.', 'danger')
        print(f"Erro ao finalizar compra: {e}")
        return redirect(url_for('cart.ver_carrinho'))
    finally:
        conn.close()

@checkout_bp.route('/confirmacao-pedido/<int:pedido_id>')
@login_required
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
        return redirect(url_for('main.home'))

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
                             'itens': itens
                         })