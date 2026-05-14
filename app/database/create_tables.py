import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.models import Base
from app.database.connection import engine
from app.database.migrations import run_admin_rbac_migrations

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    run_admin_rbac_migrations(engine)
    print("Tables created successfully")

