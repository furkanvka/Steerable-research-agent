import os
from app.core.config import settings

db_dir = os.path.dirname(settings.DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

checkpoint_db_path = os.path.join(db_dir, "lsa_checkpoints.db") if db_dir else "lsa_checkpoints.db"
