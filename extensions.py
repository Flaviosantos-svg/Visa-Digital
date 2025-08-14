from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import MetaData

# --- Configuração da Convenção de Nomes para o Alembic ---
# Isso resolve erros com o SQLite durante as migrações.
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Crie as instâncias das extensões aqui, sem associar a um 'app'.
# A associação será feita no ficheiro principal 'app.py'.
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate(render_as_batch=True)