# Arquivo: create_db.py

from app import app
from extensions import db

print("Iniciando a criação do banco de dados...")

# O app_context garante que a aplicação Flask está 'ativa' durante a operação
with app.app_context():
    # Este comando lê todos os seus modelos em models.py e cria as tabelas
    db.create_all()

print("Banco de dados e todas as tabelas foram criados com sucesso!")