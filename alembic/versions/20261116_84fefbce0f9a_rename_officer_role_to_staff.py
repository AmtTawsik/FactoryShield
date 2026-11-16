"""rename officer role to staff

Revision ID: 84fefbce0f9a
Revises: baa779ab85a7
Create Date: 2026-11-16 16:12:01.873009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84fefbce0f9a'
down_revision: Union[str, Sequence[str], None] = 'baa779ab85a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_users_user_role"), "users", type_="check")
    op.execute("UPDATE users SET role = 'staff' WHERE role = 'officer'")
    op.alter_column(
        "users",
        "role",
        type_=sa.String(length=5),
        existing_type=sa.String(length=7),
        server_default="staff",
    )
    op.create_check_constraint(op.f("ck_users_user_role"), "users", "role IN ('admin', 'staff')")


def downgrade() -> None:
    op.drop_constraint(op.f("ck_users_user_role"), "users", type_="check")
    op.alter_column(
        "users",
        "role",
        type_=sa.String(length=7),
        existing_type=sa.String(length=5),
        server_default="officer",
    )
    op.execute("UPDATE users SET role = 'officer' WHERE role = 'staff'")
    op.create_check_constraint(op.f("ck_users_user_role"), "users", "role IN ('admin', 'officer')")
