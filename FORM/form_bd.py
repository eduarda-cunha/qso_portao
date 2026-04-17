import sqlite3

def init_db():
    conn = sqlite3.connect('qsoportao.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE,
            criado_por TEXT,
            data TEXT, 
            pulseira TEXT,
            hora_entrada TEXT, 
            hora_saida TEXT, 
            portao TEXT, 
            setor TEXT,
            nome_prestador TEXT NOT NULL, 
            rg TEXT, 
            cpf TEXT, 
            data_nascimento TEXT,
            cnh_numero TEXT,
            cnh_categoria TEXT, 
            cnh_vencimento TEXT,
            empresa TEXT,
            veiculo TEXT, 
            placa TEXT, 
            servico TEXT, 
            destino_entrega TEXT NOT NULL,
            colaborador_acompanhou TEXT, 
            pulseira_acompanhante TEXT, 
            colaborador_setor TEXT,
            observacoes TEXT,
            colaboradores_json TEXT,
            assinatura_path TEXT,
            assinatura_acompanhante_path TEXT
        )
    ''')
    
    colunas_para_verificar = [
        'pulseira', 'portao', 'setor', 'cnh_numero', 'cnh_categoria', 
        'cnh_vencimento', 'colaborador_acompanhou', 'pulseira_acompanhante',
        'colaborador_setor', 'observacoes', 'empresa', 'assinatura_path', 
        'assinatura_acompanhante_path', 'colaboradores_json'
    ]
    
    for coluna in colunas_para_verificar:
        try:
            cursor.execute(f'ALTER TABLE registros ADD COLUMN {coluna} TEXT')
        except sqlite3.OperationalError:
            pass
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Banco de dados 'qsoportao.db' atualizado com sucesso!")