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
    if not b64_data:
        return None
    
    if b64_data.startswith("JUSTIFICATIVA:"):
        return b64_data 
    
    if "," in b64_data:
        try:
            nome_arquivo = f"sign_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
            header, encoded = b64_data.split(",", 1)
            
            caminho_completo = os.path.join(app.root_path, 'static', 'assinaturas', nome_arquivo)
            
            with open(caminho_completo, "wb") as f:
                f.write(base64.b64decode(encoded))
            return nome_arquivo
        except Exception as e:
            print(f"Erro ao salvar imagem: {e}")
            return None
            
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
    # comando que não limpa o quadro de qso diarios, para apenas o gestor ver todos 
    hoje_iso = datetime.now().strftime('%Y-%m-%d')

    query = '''
        SELECT * FROM registros 
        WHERE criado_por = ? AND data = ? 
        ORDER BY id DESC
    '''
    rows = db.execute(query, (session['usuario'], hoje_iso)).fetchall()
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
            'hora_entrada': request.form.get('hora_entrada'),
            'nome_prestador': request.form.get('nome_prestador'),
            'servico': request.form.get('servico'),
            'destino_entrega': request.form.get('destino_entrega'),
            'empresa': request.form.get('empresa'),
            'pulseira': request.form.get('pulseira'), 
            'cpf': request.form.get('cpf'),
            'rg': request.form.get('rg'),
            'data_nascimento': request.form.get('data_nascimento'),
            'colaborador_setor': request.form.get('colaborador_setor'),
            'portao': request.form.get('portao'),
            'setor': request.form.get('setor'),
            'veiculo': request.form.get('veiculo'),
            'placa': request.form.get('placa'),
            'hora_saida': request.form.get('hora_saida'),
            'cnh_numero': request.form.get('cnh_numero'),
            'cnh_vencimento': request.form.get('cnh_vencimento'),
            'cnh_categoria': request.form.get('cnh_categoria'),
            'observacoes': request.form.get('observacoes'),
            'colaboradores_json': request.form.get('colaboradores_json'),
            'pulseira_acompanhante': request.form.get('pulseira_acompanhante'), 
            'ass_pre': request.form.get('assinatura_data'),
            'ass_aco': request.form.get('assinatura_acompanhante')
        }

        if id:
            h_saida = dados['hora_saida'] if dados['hora_saida'] else datetime.now().strftime('%H:%M')
            db.execute('''UPDATE registros SET 
                          hora_saida = ?, empresa = ?, pulseira = ?, cpf = ?, data_nascimento = ?, 
                          portao = ?, setor = ?, colaborador_setor = ?, servico = ?, destino_entrega = ?,
                          cnh_numero = ?, cnh_vencimento = ?, cnh_categoria = ?, 
                          observacoes = ?, colaboradores_json = ?, pulseira_acompanhante = ? 
                          WHERE id = ?''', 
                       (h_saida, dados['empresa'], dados['pulseira'], dados['cpf'], dados['data_nascimento'], 
                        dados['portao'], dados['setor'], dados['colaborador_setor'], dados['servico'], dados['destino_entrega'],
                        dados['cnh_numero'], dados['cnh_vencimento'], dados['cnh_categoria'], 
                        dados['observacoes'], dados['colaboradores_json'], dados['pulseira_acompanhante'], id))
        else:
            campos = {
                'uuid': str(uuid.uuid4()), 
                'criado_por': session.get('usuario'),
                'data': dados['data'], 
                'hora_entrada': dados['hora_entrada'],
                'portao': dados['portao'], 
                'setor': dados['setor'],
                'nome_prestador': dados['nome_prestador'], 
                'rg': dados['rg'],
                'cpf': dados['cpf'], 
                'data_nascimento': dados['data_nascimento'],
                'cnh_numero': dados['cnh_numero'],
                'cnh_categoria': dados['cnh_categoria'],
                'cnh_vencimento': dados['cnh_vencimento'], 
                'empresa': dados['empresa'],
                'pulseira': dados['pulseira'],
                'veiculo': dados['veiculo'], 
                'placa': dados['placa'],
                'servico': dados['servico'], 
                'destino_entrega': dados['destino_entrega'],
                'colaboradores_json': dados['colaboradores_json'], 
                'pulseira_acompanhante': dados['pulseira_acompanhante'], 
                'colaborador_setor': dados['colaborador_setor'], 
                'observacoes': dados['observacoes'],
                'assinatura_path': salvar_assinatura(dados['ass_pre']),
                'assinatura_acompanhante_path': salvar_assinatura(dados['ass_aco'])
            }
            colunas = ', '.join(campos.keys())
            placeholders = ', '.join(['?'] * len(campos))
            db.execute(f"INSERT INTO registros ({colunas}) VALUES ({placeholders})", tuple(campos.values()))

        db.commit()
        db.close()
        return redirect(url_for('index'))

    is_fechado = False
    if registro:
            # Verifica se o campo de assinatura do prestador ou a hora de saída já existem
            if registro['assinatura_path'] or registro['hora_saida']:
                is_fechado = True

    return render_template(
        'formulario.html',
        reg=registro,
        fechado=is_fechado,
        hoje_iso=datetime.now().strftime('%Y-%m-%d')
    )

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

        fmt_aberto = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        fmt_fechado = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        
        for i, col in enumerate(df.columns):
            max_conteudo = df[col].apply(lambda x: len(str(x)) if x is not None and str(x) != 'nan' else 0).max()
            max_titulo = len(str(col))
            max_len = max(max_conteudo, max_titulo) + 2
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