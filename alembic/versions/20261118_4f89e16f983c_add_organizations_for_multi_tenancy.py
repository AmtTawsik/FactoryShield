"""add organizations for multi-tenancy

Revision ID: 4f89e16f983c
Revises: 931b6fc441af
Create Date: 2026-11-18 16:20:00.000000

Existing users, factories and factory documents move into one organization, "Default organization".
Documents without a factory stay in the shared library.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f89e16f983c'
down_revision: Union[str, Sequence[str], None] = '931b6fc441af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ORGANIZATION = "Default organization"


def upgrade() -> None:
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_organizations')),
    )
    op.create_index('uq_organizations_name_lower', 'organizations', [sa.text('lower(name)')], unique=True)

    for table in ('users', 'factories', 'knowledge_documents'):
        op.add_column(table, sa.Column('organization_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            op.f(f'fk_{table}_organization_id_organizations'), table, 'organizations', ['organization_id'], ['id']
        )
        op.create_index(op.f(f'ix_{table}_organization_id'), table, ['organization_id'], unique=False)

    # Existing data belongs to one customer: put it into a default organization.
    op.execute(
        f"""
        INSERT INTO organizations (name)
        SELECT '{DEFAULT_ORGANIZATION}'
        WHERE EXISTS (SELECT 1 FROM users) OR EXISTS (SELECT 1 FROM factories)
        """
    )
    op.execute(f"UPDATE users SET organization_id = (SELECT id FROM organizations WHERE name = '{DEFAULT_ORGANIZATION}')")
    op.execute(
        f"UPDATE factories SET organization_id = (SELECT id FROM organizations WHERE name = '{DEFAULT_ORGANIZATION}')"
    )
    op.execute(
        """
        UPDATE knowledge_documents AS d SET organization_id = f.organization_id
        FROM factories AS f WHERE d.factory_id = f.id
        """
    )
    op.alter_column('factories', 'organization_id', nullable=False)

    op.drop_constraint(op.f('uq_factories_license_number'), 'factories', type_='unique')
    op.create_unique_constraint(
        'uq_factories_organization_id_license_number', 'factories', ['organization_id', 'license_number']
    )

    op.drop_constraint(op.f('ck_users_user_role'), 'users', type_='check')
    op.alter_column('users', 'role', type_=sa.String(length=11), existing_type=sa.String(length=5))
    op.create_check_constraint(op.f('ck_users_user_role'), 'users', "role IN ('super_admin', 'admin', 'staff')")
    op.create_check_constraint(
        op.f('ck_users_organization_matches_role'), 'users', "(role = 'super_admin') = (organization_id IS NULL)"
    )
    op.create_check_constraint(
        op.f('ck_knowledge_documents_factory_document_has_organization'),
        'knowledge_documents',
        'factory_id IS NULL OR organization_id IS NOT NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f('ck_knowledge_documents_factory_document_has_organization'), 'knowledge_documents', type_='check'
    )
    op.drop_constraint(op.f('ck_users_organization_matches_role'), 'users', type_='check')
    op.drop_constraint(op.f('ck_users_user_role'), 'users', type_='check')
    op.execute("DELETE FROM users WHERE role = 'super_admin'")
    op.alter_column('users', 'role', type_=sa.String(length=5), existing_type=sa.String(length=11))
    op.create_check_constraint(op.f('ck_users_user_role'), 'users', "role IN ('admin', 'staff')")

    # Fails if two organizations hold the same licence number; those rows must be merged by hand first.
    op.drop_constraint('uq_factories_organization_id_license_number', 'factories', type_='unique')
    op.create_unique_constraint(op.f('uq_factories_license_number'), 'factories', ['license_number'])

    for table in ('knowledge_documents', 'factories', 'users'):
        op.drop_index(op.f(f'ix_{table}_organization_id'), table_name=table)
        op.drop_constraint(op.f(f'fk_{table}_organization_id_organizations'), table, type_='foreignkey')
        op.drop_column(table, 'organization_id')

    op.drop_index('uq_organizations_name_lower', table_name='organizations')
    op.drop_table('organizations')
