from flask import Blueprint, render_template, session, flash, redirect, url_for
from database import conectar_db
from utils.decorators import login_required
import sqlite3
import datetime # Importar o módulo datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/meus-pedidos')
@login_required
def historico_pedidos():
    """
    Exibe o histórico de pedidos do usuário logado.
    """
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        flash("Por favor, faça login para ver seus pedidos.", "info")
        return redirect(url_for('auth.login'))

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # Busca os pedidos do usuário
        cursor.execute('''
            SELECT id, data, status, total
            FROM pedidos
            WHERE usuario_id = ?
            ORDER BY data DESC
        ''', (usuario_id,))
        
        pedidos_raw = cursor.fetchall()
        pedidos = []
        for p_raw in pedidos_raw:
            pedido = dict(p_raw)
            # Converte a string 'data' para um objeto datetime
            # O formato esperado de SQLite é 'YYYY-MM-DD HH:MM:SS'
            if 'data' in pedido and isinstance(pedido['data'], str):
                try:
                    pedido['data'] = datetime.datetime.strptime(pedido['data'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Lida com casos onde o formato da data pode ser ligeiramente diferente
                    print(f"Formato de data inesperado para o pedido {pedido['id']}: {pedido['data']}")
                    # Mantém como string ou define como None para evitar erro
            pedidos.append(pedido)


        # Para cada pedido, busca os itens do pedido
        for pedido in pedidos:
            cursor.execute('''
                SELECT pi.quantidade, pi.preco_unitario, p.nome, p.imagem
                FROM pedido_itens pi
                JOIN produtos p ON pi.produto_id = p.id
                WHERE pi.pedido_id = ?
            ''', (pedido['id'],))
            
            # Converte os objetos sqlite3.Row em dicionários mutáveis para os itens do pedido também
            pedido_itens_raw = cursor.fetchall()
            pedido['itens'] = [dict(item) for item in pedido_itens_raw]

    except sqlite3.Error as e:
        flash(f"Erro no banco de dados ao buscar pedidos: {e}", "danger")
        print(f"Database error in historico_pedidos: {e}")
        pedidos = [] # Retorna lista vazia em caso de erro
    except Exception as e:
        flash(f"Ocorreu um erro inesperado ao buscar pedidos: {e}", "danger")
        print(f"Unexpected error in historico_pedidos: {e}")
        pedidos = []
    finally:
        conn.close()

    return render_template('historico_pedidos.html', pedidos=pedidos)
