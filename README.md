# qso_portao
Este é um sistema web desenvolvido em Python/Flask para o gerenciamento e registro de entrada e saída de prestadores de serviço e visitantes. O sistema permite o controle por pulseiras, coleta de assinaturas digitais e geração de relatórios em Excel.

🚀 Funcionalidades
Registro de Entrada: Captura de dados do prestador, empresa, veículo, placa e número da pulseira.

Assinatura Digital: Coleta de assinatura via tela (touch/mouse) para o prestador e o colaborador responsável.

Gestão de Saída: Atualização rápida do horário de saída para registros em aberto.

Painel Administrativo: Filtros por data, colaborador e status do registro.

Relatórios: Exportação de dados filtrados diretamente para arquivos .xlsx (Excel).

Segurança: Área de gestão protegida por autenticação.

🛠️ Tecnologias Utilizadas
Backend: Python 3 + Flask

Banco de Dados: SQLite (leve e sem necessidade de servidor externo)

Frontend: HTML5, CSS3, JavaScript

Bibliotecas JS: SignaturePad (assinaturas digitais)

Bibliotecas Python: Pandas e XlsxWriter (processamento de dados e Excel)

Hospedagem: Render

📁 Estrutura do Projeto
Plaintext
QSO_PORTAO/
├── FORM/                # Pasta principal do código
│   ├── static/          # Arquivos CSS, imagens e assinaturas salvas
│   ├── templates/       # Páginas HTML do sistema
│   └── app.py           # Arquivo principal (Backend)
├── requirements.txt     # Dependências para o deploy
└── README.md            # Documentação do projeto
