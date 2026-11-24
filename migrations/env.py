"""执行当前服务的 Alembic 迁移。"""

from alembic import context

from app.core.config import MigrationSettings
from app.core.database import AUTH_SCHEMA, database_engine

url = MigrationSettings().migration_database_url
if url is None:
    raise SystemExit("请设置 MIGRATION_DATABASE_URL。")
engine = database_engine(url.get_secret_value())
if context.is_offline_mode():
    context.configure(dialect_name="postgresql", version_table_schema=AUTH_SCHEMA)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, version_table_schema=AUTH_SCHEMA)
        with context.begin_transaction():
            context.run_migrations()
