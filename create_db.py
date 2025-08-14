<<<<<<< HEAD
# Arquivo: create_db.py

from app import app
from extensions import db

print("Iniciando a criação do banco de dados...")

# O app_context garante que a aplicação Flask está 'ativa' durante a operação
with app.app_context():
    # Este comando lê todos os seus modelos em models.py e cria as tabelas
    db.create_all()

=======
# Arquivo: create_db.py

from app import app
from extensions import db

print("Iniciando a criação do banco de dados...")

# O app_context garante que a aplicação Flask está 'ativa' durante a operação
with app.app_context():
    # Este comando lê todos os seus modelos em models.py e cria as tabelas
    db.create_all()

>>>>>>> 8eb43a47d2edf7657b5b37831d9a03f100985590
print("Banco de dados e todas as tabelas foram criados com sucesso!")