from flask import Flask, render_template, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
import sqlite3
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "seguranca_praia_clube"
auth = HTTPBasicAuth()

users = {"admin": "praia2024"}

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
    'veiculo', 'placa', 'servico', 'destino_entrega', 'colaborador_acompanhou', 'colaborador_setor'
]

OBRIGATORIOS = [
    'portao', 'setor', 'nome_prestador', 'cpf', 'data_nascimento', 
    'empresa', 'servico', 'colaborador_setor', 'data', 'destino_entrega'
]

@app.route('/')
def index():
    db = get_db()
    registros = db.execute('SELECT * FROM registros ORDER BY id DESC LIMIT 20').fetchall()
    db.close()
    hoje = datetime.now().strftime('%d/%m/%Y')
    return render_template('index.html', registros=registros, hoje=hoje)

@app.route('/formulario')
@app.route('/formulario/<id_unico>')
def formulario(id_unico=None):
    db = get_db()
    registro = None
    if id_unico:
        registro = db.execute('SELECT * FROM registros WHERE uuid = ?', (id_unico,)).fetchone()
    db.close()
    return render_template('formulario.html', reg=registro)

@app.route('/add', methods=['POST'])
def add():
    for campo in OBRIGATORIOS:
        if not request.form.get(campo):
            return f"Erro: O campo {campo.upper()} é obrigatório!", 400
    codigo = str(uuid.uuid4())[:8]
    dados = [codigo] + [request.form.get(f) for f in CAMPOS]
    db = get_db()
    placeholder = ",".join(["?"] * 20)
    db.execute(f'INSERT INTO registros (uuid, {", ".join(CAMPOS)}) VALUES ({placeholder})', dados)
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/edit/<id_unico>', methods=['POST'])
def edit(id_unico):
    for campo in OBRIGATORIOS:
        if not request.form.get(campo):
            return f"Erro: O campo {campo.upper()} é obrigatório!", 400
    db = get_db()
    set_query = ", ".join([f"{f} = ?" for f in CAMPOS])
    dados = [request.form.get(f) for f in CAMPOS] + [id_unico]
    db.execute(f'UPDATE registros SET {set_query} WHERE uuid = ?', dados)
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/gestao')
@auth.login_required
def gestao():
    db = get_db()
    registros = db.execute('SELECT * FROM registros ORDER BY id DESC').fetchall()
    db.close()
    return render_template('gestao.html', registros=registros)

@app.route('/registro/<id_unico>')
def ver_registro(id_unico):
    db = get_db()
    registro = db.execute('SELECT * FROM registros WHERE uuid = ?', (id_unico,)).fetchone()
    db.close()
    return render_template('registro_unico.html', reg=registro) if registro else ("Não encontrado", 404)

if __name__ == '__main__':
    app.run(debug=True)