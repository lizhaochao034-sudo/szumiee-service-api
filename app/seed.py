"""在本地联调库中创建或更新一个测试账号。"""

import argparse
import os
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import MigrationSettings
from app.core.database import ROLES, account_table, database_engine
from app.core.security import password_hasher


def main() -> None:
    """通过登录名写入测试账号，保留已有 ID 并使旧会话失效。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", choices=ROLES, required=True)
    args = parser.parse_args()
    login_name = args.username.strip()
    name = args.name.strip()
    password = os.environ.get("SEED_PASSWORD", "")
    if not 1 <= len(login_name) <= 128 or not 1 <= len(name) <= 128:
        parser.error("登录名和姓名长度均须为 1 至 128 个字符。")
    if "\x00" in login_name or "\x00" in name:
        parser.error("登录名和姓名不能包含空字符。")
    if not 1 <= len(password) <= 1024:
        parser.error("SEED_PASSWORD 长度须为 1 至 1024 个字符。")
    url = MigrationSettings().migration_database_url
    if url is None:
        parser.error("请设置 MIGRATION_DATABASE_URL。")
    values = {
        "name": name,
        "password_hash": password_hasher.hash(password),
        "roles": [args.role],
        "session_id": None,
    }
    statement = insert(account_table).values(
        account_id=uuid4(), username=login_name, **values
    ).on_conflict_do_update(index_elements=[account_table.c.username], set_=values)
    try:
        engine = database_engine(url.get_secret_value())
        with engine.begin() as connection:
            connection.execute(statement)
    except (SQLAlchemyError, ValueError):
        parser.exit(1, "写入测试账号失败，请检查迁移配置和账号表。\n")
    print("测试账号已写入。")


if __name__ == "__main__":
    main()
