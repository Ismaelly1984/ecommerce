from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from database import conectar_db, calcular_total_carrinho_db, get_produto_por_id
from utils.decorators import login_required
import sqlite3

# Crie um Blueprint para as rotas de checkout
checkout_bp = Blueprint('checkout', __name__)

@checkout_bp.route('/finalizar_compra')
@login_required
def finalizar_compra():
    """
    Exibe a página de finalização de compra com os detalhes do carrinho.
    """
    usuario_id = session['usuario_id']
    total_carrinho, total_itens_no_carrinho = calcular_total_carrinho_db(usuario_id)

    if total_itens_no_carrinho == 0:
        flash('Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.', 'info')
        return redirect(url_for('main.home'))

    conn = conectar_db()
    cursor = conn.cursor()

    # Pega os itens do carrinho com detalhes do produto
    cursor.execute('''
        SELECT c.produto_id, c.quantidade, p.nome, p.preco, p.imagem, p.estoque
        FROM carrinho c
        JOIN produtos p ON c.produto_id = p.id
        WHERE c.usuario_id = ?
    ''', (usuario_id,))
    itens_carrinho = cursor.fetchall()
    conn.close()

    return render_template('checkout.html', 
                           itens_carrinho=itens_carrinho, 
                           total_carrinho=total_carrinho)

@checkout_bp.route('/processar_pagamento', methods=['POST'])
@login_required
def processar_pagamento():
    """
    Processa o pagamento e finaliza o pedido.
    """
    usuario_id = session['usuario_id']
    total_carrinho, total_itens_no_carrinho = calcular_total_carrinho_db(usuario_id)

    if total_itens_no_carrinho == 0:
        flash('Seu carrinho está vazio. Não é possível processar um pedido vazio.', 'danger')
        return redirect(url_for('cart.ver_carrinho'))

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # 1. Criar um novo pedido
        cursor.execute('''
            INSERT INTO pedidos (usuario_id, total, status)
            VALUES (?, ?, ?)
        ''', (usuario_id, total_carrinho, 'Processando'))
        pedido_id = cursor.lastrowid # Obtém o ID do pedido recém-criado

        # 2. Mover itens do carrinho para itens do pedido
        cursor.execute('''
            SELECT c.produto_id, c.quantidade, p.preco, p.nome, p.estoque
            FROM carrinho c
            JOIN produtos p ON c.produto_id = p.id
            WHERE c.usuario_id = ?
        ''', (usuario_id,))
        itens_carrinho = cursor.fetchall()

        for item in itens_carrinho:
            # Insere o item na tabela pedido_itens
            cursor.execute('''
                INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
            ''', (pedido_id, item['produto_id'], item['quantidade'], item['preco']))

            # 3. Atualizar estoque do produto
            novo_estoque = item['estoque'] - item['quantidade']
            cursor.execute('UPDATE produtos SET estoque = ? WHERE id = ?', (novo_estoque, item['produto_id']))
        
        # 4. Limpar o carrinho do usuário
        cursor.execute('DELETE FROM carrinho WHERE usuario_id = ?', (usuario_id,))

        conn.commit()
        flash(f'Pedido {pedido_id} realizado com sucesso! Em breve você receberá um e-mail de confirmação.', 'success')
        return redirect(url_for('user.historico_pedidos')) # Redireciona para o histórico de pedidos

    except sqlite3.Error as e:
        conn.rollback() # Reverte as operações em caso de erro
        print(f"Erro no banco de dados ao finalizar compra: {e}")
        flash(f'Ocorreu um erro ao finalizar sua compra. Por favor, tente novamente. Erro: {e}', 'danger')
        return redirect(url_for('checkout.finalizar_compra'))
    except Exception as e:
        conn.rollback()
        print(f"Erro inesperado ao finalizar compra: {e}")
        flash(f'Ocorreu um erro inesperado. Por favor, tente novamente. Erro: {e}', 'danger')
        return redirect(url_for('checkout.finalizar_compra'))
    finally:
        conn.close()
