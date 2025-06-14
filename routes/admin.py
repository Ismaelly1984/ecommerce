from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import conectar_db, registrar_log
from utils.decorators import admin_required
from utils.helpers import allowed_file
from werkzeug.utils import secure_filename
import os
from config import Config # Para acessar UPLOAD_FOLDER

admin_bp = Blueprint('admin', __name__, url_prefix='/admin') # Prefixo de URL para todas as rotas admin

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM produtos')
    total_produtos = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM usuarios')
    total_usuarios = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE DATE(data) = DATE('now', '-3 hours')")
    pedidos_hoje = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos WHERE strftime('%Y-%m', data, '-3 hours') = strftime('%Y-%m', 'now', '-3 hours')")
    vendas_mensais = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    vendas_totais = cursor.fetchone()[0]

    cursor.execute('''
        SELECT p.id, u.nome as cliente, p.data, p.total, p.status
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.data DESC
        LIMIT 5
    ''')
    ultimos_pedidos = cursor.fetchall()

    cursor.execute('SELECT nome, estoque FROM produtos WHERE estoque < 10 ORDER BY estoque ASC LIMIT 5')
    estoque_baixo = cursor.fetchall()

    conn.close()

    return render_template('admin/dashboard.html',
                         total_produtos=total_produtos,
                         total_usuarios=total_usuarios,
                         pedidos_hoje=pedidos_hoje,
                         vendas_mensais=vendas_mensais,
                         vendas_totais=vendas_totais,
                         ultimos_pedidos=ultimos_pedidos,
                         estoque_baixo=estoque_baixo)

@admin_bp.route('/produtos')
@admin_required
def admin_produtos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos ORDER BY nome')
    produtos = cursor.fetchall()
    conn.close()
    return render_template('admin/produtos.html', produtos=produtos)

@admin_bp.route('/novo_produto', methods=['GET', 'POST'])
@admin_required
def novo_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])
        descricao = request.form['descricao']
        imagem_filename = None

        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(Config.UPLOAD_FOLDER, filename)) # Usar Config.UPLOAD_FOLDER
                imagem_filename = filename

        conn = conectar_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO produtos (nome, preco, estoque, descricao, imagem)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, preco, estoque, descricao, imagem_filename))
            conn.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('admin.admin_produtos'))
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao adicionar produto: {e}', 'danger')
        finally:
            conn.close()
    return render_template('admin/novo_produto.html')

@admin_bp.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_produto(id):
    conn = conectar_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])
        descricao = request.form['descricao']

        imagem_filename = request.form.get('imagem_existente')
        if 'imagem' in request.files and request.files['imagem'].filename != '':
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(Config.UPLOAD_FOLDER, filename)) # Usar Config.UPLOAD_FOLDER
                imagem_filename = filename

        try:
            cursor.execute('''
                UPDATE produtos
                SET nome=?, preco=?, estoque=?, descricao=?, imagem=?
                WHERE id=?
            ''', (nome, preco, estoque, descricao, imagem_filename, id))

            conn.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('admin.admin_produtos'))
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao atualizar produto: {e}', 'danger')
        finally:
            conn.close()
    else: # GET request
        cursor.execute('SELECT * FROM produtos WHERE id = ?', (id,))
        produto = cursor.fetchone()
        conn.close()

        if not produto:
            flash('Produto não encontrado', 'danger')
            return redirect(url_for('admin.admin_produtos'))

        return render_template('admin/editar_produto.html', produto=produto)

@admin_bp.route('/produtos/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_produto(id):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM produtos WHERE id = ?', (id,))
        conn.commit()
        flash('Produto excluído com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao excluir produto: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin.admin_produtos'))

@admin_bp.route('/pedidos')
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

@admin_bp.route('/pedidos/<int:id>')
@admin_required
def detalhes_pedido(id):
    conn = conectar_db()
    cursor = conn.cursor()
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
        return redirect(url_for('admin.admin_pedidos'))

    cursor.execute('''
        SELECT pi.quantidade, pi.preco_unitario, pr.nome, pr.id
        FROM pedido_itens pi
        JOIN produtos pr ON pi.produto_id = pr.id
        WHERE pi.pedido_id = ?
    ''', (id,))
    itens = cursor.fetchall()
    conn.close()

    return render_template('admin/detalhes_pedido.html', pedido=pedido, itens=itens)

@admin_bp.route('/pedidos/atualizar-status/<int:id>', methods=['POST'])
@admin_required
def atualizar_status_pedido(id):
    novo_status = request.form['status']
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE pedidos
            SET status = ?
            WHERE id = ?
        ''', (novo_status, id))
        conn.commit()
        flash('Status do pedido atualizado com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao atualizar status do pedido: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin.detalhes_pedido', id=id))

@admin_bp.route('/usuarios')
@admin_required
def admin_usuarios():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, email, is_admin FROM usuarios ORDER BY nome')
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/toggle_admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin_status(user_id):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT is_admin FROM usuarios WHERE id = ?', (user_id,))
        current_status = cursor.fetchone()['is_admin']
        new_status = not bool(current_status)

        cursor.execute('UPDATE usuarios SET is_admin = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        flash(f'Status de administrador do usuário atualizado para {"Admin" if new_status else "Usuário Comum"}.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao alterar status de admin: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('admin.admin_usuarios'))

@admin_bp.route('/logs')
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