from flask import Blueprint, render_template, session, flash, redirect, url_for
from database import conectar_db
from utils.decorators import login_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/historico-pedidos')
@login_required
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
        ''', (pedido['id'],))

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