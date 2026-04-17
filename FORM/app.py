import os
import sqlite3
import pandas as pd
import base64
import json
import uuid
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_httpauth import HTTPBasicAuth

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
    conn.row_factory = sqlite3.Row  
    return conn

users = {"admin": "praia11037"}

@auth.verify_password
def verify_password(username, password):
    if username in users and users.get(username) == password:
        return username

def salvar_assinatura(b64_data):
    if b64_data and "," in b64_data:
        nome_arquivo = f"sign_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
        header, encoded = b64_data.split(",", 1)
        with open(os.path.join(UPLOAD_FOLDER, nome_arquivo), "wb") as f:
            f.write(base64.b64decode(encoded))
        return nome_arquivo
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_raw = request.form.get('chave_acesso') or request.form.get('usuario')
        if usuario_raw and usuario_raw.strip():
            session['usuario'] = usuario_raw.strip().lower()
            return redirect(url_for('index'))
        return render_template('login.html', erro="Usuário inválido.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'usuario' not in session: 
        return redirect(url_for('login'))
    db = get_db()
    rows = db.execute('SELECT * FROM registros WHERE criado_por = ? ORDER BY id DESC', (session['usuario'],)).fetchall()
    registros = [dict(row) for row in rows] 
    db.close()
    return render_template('index.html', registros=registros, hoje=datetime.now().strftime('%d/%m/%Y'))

@app.route('/formulario', methods=['GET', 'POST'])
@app.route('/formulario/<int:id>', methods=['GET', 'POST'])
def formulario(id=None):
    if 'usuario' not in session: return redirect(url_for('login'))
    db = get_db()
    registro = None
    if id:
        registro = db.execute('SELECT * FROM registros WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        dados = {
            'data': request.form.get('data'),
            'h_entrada': request.form.get('hora_entrada'),
            'nome': request.form.get('nome_prestador'),
            'servico': request.form.get('servico'),
            'destino': request.form.get('destino_entrega'),
            'empresa': request.form.get('empresa'),
            'cpf': request.form.get('cpf'),
            'rg': request.form.get('rg'),
            'nascimento': request.form.get('data_nascimento'),
            'colab_setor': request.form.get('colaborador_setor'),
            'portao': request.form.get('portao'),
            'setor': request.form.get('setor'),
            'veiculo': request.form.get('veiculo'),
            'placa': request.form.get('placa'),
            'h_saida': request.form.get('hora_saida'),
            'cnh_n': request.form.get('cnh_numero'),
            'cnh_v': request.form.get('cnh_vencimento'),
            'cnh_c': request.form.get('cnh_categoria'),
            'obs': request.form.get('observacoes'),
            'ajudantes': request.form.get('colaboradores_json'),
            'ass_pre': request.form.get('assinatura_data'),
            'ass_aco': request.form.get('assinatura_acompanhante')
        }

        if id:
            hora_final = dados['h_saida'] if dados['h_saida'] else datetime.now().strftime('%H:%M')
            db.execute('''UPDATE registros SET 
                          hora_saida = ?, cpf = ?, data_nascimento = ?, portao = ?, 
                          setor = ?, colaborador_setor = ?, servico = ?, destino_entrega = ?,
                          cnh_numero = ?, cnh_vencimento = ?, cnh_categoria = ?, 
                          observacoes = ?, colaborador_acompanhou = ? 
                          WHERE id = ?''', 
                       (hora_final, dados['cpf'], dados['nascimento'], dados['portao'], 
                        dados['setor'], dados['colab_setor'], dados['servico'], dados['destino'],
                        dados['cnh_n'], dados['cnh_v'], dados['cnh_c'], dados['obs'], 
                        dados['ajudantes'], id))
        else:
            campos = {
                'uuid': str(uuid.uuid4()), 
                'criado_por': session.get('usuario'),
                'data': dados.get('data'), 
                'hora_entrada': dados.get('h_entrada'),
                'portao': dados.get('portao'), 
                'setor': dados.get('setor'),
                'nome_prestador': dados.get('nome'), 
                'rg': dados.get('rg'),
                'cpf': dados.get('cpf'), 
                'data_nascimento': dados.get('nascimento'),
                'cnh': dados.get('cnh_n'), 
                'categoria': dados.get('cnh_c'),
                'vencimento_cnh': dados.get('cnh_v'), 
                'empresa': dados.get('empresa'),
                'veiculo': dados.get('veiculo'), 
                'placa': dados.get('placa'),
                'servico': dados.get('servico'), 
                'destino_entrega': dados.get('destino'),
                'colaborador_acompanhou': dados.get('ajudantes'), 
                'colaborador_setor': dados.get('colab_setor'), 
                'observacoes': dados.get('obs'),
                'assinatura_path': salvar_assinatura(dados['ass_pre']),
                'assinatura_acompanhante_path': salvar_assinatura(dados['ass_aco'])
            }
            colunas = ', '.join(campos.keys())
            placeholders = ', '.join(['?'] * len(campos))
            db.execute(f"INSERT INTO registros ({colunas}) VALUES ({placeholders})", tuple(campos.values()))

        db.commit()
        db.close()
        return redirect(url_for('index'))

    return render_template('formulario.html', reg=registro, hoje_iso=datetime.now().strftime('%Y-%m-%d'))

@app.route('/gestor')
@auth.login_required
def gestor():
    db = get_db()
    d_inicio = request.args.get('data_inicio')
    d_fim = request.args.get('data_fim')
    colab = request.args.get('colaborador')
    status = request.args.get('status', 'todos')

    query = "SELECT * FROM registros WHERE 1=1"
    params = []

    if d_inicio: query += " AND data >= ?"; params.append(d_inicio)
    if d_fim: query += " AND data <= ?"; params.append(d_fim)
    if colab: query += " AND criado_por LIKE ?"; params.append(f"%{colab}%")
    
    if status == 'aberto': 
        query += " AND (hora_saida IS NULL OR hora_saida = '')"
    elif status == 'fechado': 
        query += " AND (hora_saida IS NOT NULL AND hora_saida != '')"

    rows = db.execute(query + " ORDER BY id DESC", params).fetchall()
    db.close()
    return render_template('gestor.html', registros=[dict(row) for row in rows], filtros=request.args)

@app.route('/exportar')
@auth.login_required
def exportar():
    db = get_db()
    d_inicio = request.args.get('data_inicio')
    d_fim = request.args.get('data_fim')
    colab = request.args.get('colaborador')
    status = request.args.get('status', 'todos')

    query = "SELECT * FROM registros WHERE 1=1"
    params = []
    if d_inicio: query += " AND data >= ?"; params.append(d_inicio)
    if d_fim: query += " AND data <= ?"; params.append(d_fim)
    if colab: query += " AND criado_por LIKE ?"; params.append(f"%{colab}%")
    
    if status == 'aberto': 
        query += " AND (hora_saida IS NULL OR hora_saida = '')"
    elif status == 'fechado': 
        query += " AND (hora_saida IS NOT NULL AND hora_saida != '')"

    df = pd.read_sql_query(query, db, params=params)
    db.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
        
        workbook  = writer.book
        worksheet = writer.sheets['Relatorio']

        # Formatos
        fmt_aberto = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        fmt_fechado = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)

        if not df.empty:
            idx_saida = df.columns.get_loc('hora_saida')
            letra_saida = chr(65 + idx_saida) 
            ultimo_row = len(df)
            ultima_col = len(df.columns) - 1
            
            worksheet.conditional_format(1, 0, ultimo_row, ultima_col, {
                'type':     'formula',
                'criteria': f'=${letra_saida}2<>""',
                'format':   fmt_fechado
            })
            worksheet.conditional_format(1, 0, ultimo_row, ultima_col, {
                'type':     'formula',
                'criteria': f'=${letra_saida}2=""',
                'format':   fmt_aberto
            })

    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
         as_attachment=True, download_name=f"relatorio_{datetime.now().strftime('%d%m%Y')}.xlsx")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)