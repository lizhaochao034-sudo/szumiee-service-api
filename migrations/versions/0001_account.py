"""创建账号表并授予运行角色最小权限。"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0001_account"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建账号表并授权读取账号和更新当前会话。"""
    op.create_table(
        "account",
        sa.Column("account_id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(128), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("roles", ARRAY(sa.Text()), nullable=False),
        sa.Column("session_id", sa.Uuid()),
        sa.CheckConstraint(
            "cardinality(roles) > 0 AND array_ndims(roles) = 1 "
            "AND array_lower(roles, 1) = 1 "
            "AND roles <@ ARRAY['student', 'ta', 'mgmt']::text[]",
            name="ck_account_roles",
        ),
        schema="service_auth",
    )
    op.execute("GRANT USAGE ON SCHEMA service_auth TO service_login")
    op.execute("GRANT SELECT, UPDATE (session_id) ON service_auth.account TO service_login")


def downgrade() -> None:
    """删除本次迁移创建的账号表。"""
    op.drop_table("account", schema="service_auth")
