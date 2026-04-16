from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_httpauth import HTTPBasicAuth
import sqlite3
import os
import uuid
import pandas as pd
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = "seguranca_praia_clube"
auth = HTTPBasicAuth()

users = {"admin": "praia11037"}

@auth.verify_password
def verify_password(username, password):
    if username in users and users.get(username) == password:
        return username

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qsoportao.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

CAMPOS = [
    'data', 'hora_entrada', 'hora_saida', 'portao', 'setor', 'nome_prestador', 'rg', 'cpf', 
    'data_nascimento', 'cnh', 'categoria', 'vencimento_cnh', 'empresa', 
    'veiculo', 'placa', 'servico', 'destino_entrega', 'colaborador_acompanhou', 
    'colaborador_setor', 'assinatura_acompanhante', 'observacoes', 'assinatura_prestador', 
    'justificativa_falta_assinatura', 'colaboradores_adicionais'
]

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    colunas = ['id INTEGER PRIMARY KEY AUTOINCREMENT', 'uuid TEXT', 'criado_por TEXT']
    for campo in CAMPOS:
        colunas.append(f"{campo} TEXT")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS registros ({', '.join(colunas)})")
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        chave = request.form.get('chave_acesso', '').lower().strip()
        if "_" in chave:
            session['usuario'] = chave
            return redirect(url_for('index'))
        return "Erro: Use o formato nome_sobrenome", 400
    return render_template('login.html')

@app.route('/')
def index():
    if 'usuario' not in session: return redirect(url_for('login'))
    db = get_db()
    registros = db.execute('SELECT * FROM registros WHERE criado_por = ? ORDER BY id DESC', (session['usuario'],)).fetchall()
    db.close()
    hoje = datetime.now().strftime('%d/%m/%Y')
    return render_template('index.html', registros=registros, hoje=hoje)

@app.route('/formulario')
@app.route('/formulario/<id_unico>')
def formulario(id_unico=None):
    if 'usuario' not in session: return redirect(url_for('login'))
    db = get_db()
    registro = db.execute('SELECT * FROM registros WHERE uuid = ?', (id_unico,)).fetchone() if id_unico else None
    db.close()
    hoje_iso = datetime.now().strftime('%Y-%m-%d')
    return render_template('formulario.html', reg=registro, hoje_iso=hoje_iso)

@app.route('/add', methods=['POST'])
def add():
    if 'usuario' not in session: return redirect(url_for('login'))
    codigo = str(uuid.uuid4())[:8]
    dados = [codigo, session['usuario']] + [request.form.get(f, '') for f in CAMPOS]
    db = get_db()
    placeholder = ",".join(["?"] * (len(CAMPOS) + 2))
    db.execute(f'INSERT INTO registros (uuid, criado_por, {", ".join(CAMPOS)}) VALUES ({placeholder})', dados)
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/gestor')
@auth.login_required
def gestor():
    db = get_db()
    registros = db.execute('SELECT * FROM registros ORDER BY id DESC').fetchall()
    db.close()
    hoje = datetime.now().strftime('%d/%m/%Y')
    return render_template('gestor.html', registros=registros, hoje=hoje)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)