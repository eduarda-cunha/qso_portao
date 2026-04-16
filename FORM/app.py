import os
import sqlite3
import pandas as pd
import base64
import json
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_httpauth import HTTPBasicAuth

# Configuração de caminhos e pastas
base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))
app.secret_key = "seguranca_praia_clube"
auth = HTTPBasicAuth()

UPLOAD_FOLDER = os.path.join(base_dir, 'static', 'assinaturas')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

DB_PATH = os.path.join(base_dir, "qsoportao.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    return conn

# Credenciais do Gestor
users = {"admin": "praia11037"}

@auth.verify_password
def verify_password(username, password):
    if username in users and users.get(username) == password:
        return username

# --- FUNÇÃO HELPER PARA SALVAR ASSINATURA ---
def salvar_assinatura(b64_data):
    if b64_data and "," in b64_data:
        nome_arquivo = f"sign_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
        header, encoded = b64_data.split(",", 1)
        with open(os.path.join(UPLOAD_FOLDER, nome_arquivo), "wb") as f:
            f.write(base64.b64decode(encoded))
        return nome_arquivo
    return None

# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_raw = request.form.get('chave_acesso') or request.form.get('usuario')
        if usuario_raw and usuario_raw.strip():
            session['usuario'] = usuario_raw.strip().lower()
            return redirect(url_for('index'))
        else:
            return render_template('login.html', erro="Usuário inválido.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ROTA PRINCIPAL (LISTAGEM DO OPERADOR) ---
@app.route('/')
def index():
    if 'usuario' not in session: 
        return redirect(url_for('login'))
    
    db = get_db()
    rows = db.execute('SELECT * FROM registros WHERE criado_por = ? ORDER BY id DESC', (session['usuario'],)).fetchall()
    registros = [dict(row) for row in rows] # Prevenção de erro de serialização
    db.close()
    return render_template('index.html', registros=registros, hoje=datetime.now().strftime('%d/%m/%Y'))

# --- ROTA DO FORMULÁRIO (ENTRADA E SAÍDA) ---
@app.route('/formulario', methods=['GET', 'POST'])
@app.route('/formulario/<int:id>', methods=['GET', 'POST'])
def formulario(id=None):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    db = get_db()
    registro = None
    if id:
        registro = db.execute('SELECT * FROM registros WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        # Captura de dados do formulário
        dados = {
            'nome': request.form.get('nome_prestador'),
            'empresa': request.form.get('empresa'),
            'portao': request.form.get('portao'),
            'cnh_n': request.form.get('cnh_numero'),
            'cnh_v': request.form.get('cnh_vencimento'),
            'cnh_c': request.form.get('cnh_categoria'),
            'obs': request.form.get('observacoes'),
            'ajudantes': request.form.get('colaboradores_json'),
            'ass_pre': request.form.get('assinatura_data'),
            'ass_aco': request.form.get('assinatura_acompanhante'),
            'h_saida': request.form.get('hora_saida')
        }

        if id:
            # Lógica de Atualização / Saída
            hora_final = dados['h_saida'] if dados['h_saida'] else datetime.now().strftime('%H:%M')
            db.execute('''UPDATE registros SET 
                          hora_saida = ?, cnh_numero = ?, cnh_vencimento = ?, 
                          cnh_categoria = ?, observacoes = ? WHERE id = ?''', 
                       (hora_final, dados['cnh_n'], dados['cnh_v'], dados['cnh_c'], dados['obs'], id))
        else:
            # Lógica de Novo Registro
            arq_prestador = salvar_assinatura(dados['ass_pre'])
            arq_acompanhante = salvar_assinatura(dados['ass_aco'])

            db.execute('''INSERT INTO registros 
                (data, hora_entrada, nome_prestador, empresa, portao, cnh_numero, 
                 cnh_vencimento, cnh_categoria, observacoes, colaboradores_adicionais, 
                 criado_por, assinatura_path, assinatura_acompanhante_path) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%H:%M'), 
                 dados['nome'], dados['empresa'], dados['portao'], dados['cnh_n'], 
                 dados['cnh_v'], dados['cnh_c'], dados['obs'], dados['ajudantes'], 
                 session['usuario'], arq_prestador, arq_acompanhante))
        
        db.commit()
        db.close()
        return redirect(url_for('index'))

    # hoje_iso é necessário para o campo <input type="date"> funcionar
    return render_template('formulario.html', registro=registro, hoje_iso=datetime.now().strftime('%Y-%m-%d'))

# --- ROTA DO GESTOR (CORRIGIDA) ---
@app.route('/gestor')
@auth.login_required
def gestor():
    db = get_db()
    rows = db.execute('SELECT * FROM registros ORDER BY id DESC').fetchall()
    db.close()
    
    # Conversão de Row para Dict evita o erro de serialização
    registros = [dict(row) for row in rows]
    return render_template('gestor.html', registros=registros, filtros=request.args)

# --- ROTA DE EXPORTAÇÃO (CORRIGE O BUILDERROR) ---
@app.route('/exportar')
@auth.login_required
def exportar():
    db = get_db()
    query = 'SELECT * FROM registros ORDER BY id DESC'
    df = pd.read_sql_query(query, db)
    db.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio_Portaria')
    output.seek(0)

    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True, 
        download_name=f'relatorio_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True)