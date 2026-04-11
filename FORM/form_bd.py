import sqlite3

def init_db():
    conn = sqlite3.connect('qsoportao.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE,
            criado_por TEXT,
            data TEXT, hora_entrada TEXT, hora_saida TEXT, portao TEXT, setor TEXT,
            nome_prestador TEXT NOT NULL, rg TEXT, cpf TEXT, data_nascimento TEXT,
            cnh TEXT, categoria TEXT, vencimento_cnh TEXT, empresa TEXT,
            veiculo TEXT, placa TEXT, servico TEXT, destino_entrega TEXT NOT NULL,
            colaborador_acompanhou TEXT, colaborador_setor TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Banco de dados pronto!")