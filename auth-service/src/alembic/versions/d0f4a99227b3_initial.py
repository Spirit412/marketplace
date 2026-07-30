"""initial

Revision ID: d0f4a99227b3
Revises:
Create Date: 2026-07-26 17:15:26.529239
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d0f4a99227b3"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("uuid", sa.Uuid(), nullable=False, comment="pk группы"),
        sa.Column("name", sa.String(), nullable=False, comment="название группы"),
        sa.Column("description", sa.String(), nullable=True, comment="описание группы"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_groups")),
        schema="auth",
    )
    op.create_table(
        "permissions",
        sa.Column("uuid", sa.Uuid(), nullable=False, comment="pk разрешения"),
        sa.Column("name", sa.String(), nullable=False, comment="название разрешения"),
        sa.Column(
            "app_id", sa.String(), nullable=False, comment="идентификатор микросервиса"
        ),
        sa.Column("method", sa.String(), nullable=False, comment="HTTP-метод"),
        sa.Column("path", sa.String(), nullable=False, comment="путь для доступа"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_permissions")),
        schema="auth",
    )
    op.create_table(
        "roles",
        sa.Column("uuid", sa.Uuid(), nullable=False, comment="pk роли"),
        sa.Column("name", sa.String(), nullable=False, comment="название роли"),
        sa.Column("description", sa.String(), nullable=True, comment="описание роли"),
        sa.Column(
            "is_admin",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment="признак административной роли",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_roles")),
        schema="auth",
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocked_by", sa.Uuid(), nullable=True),
        sa.Column("block_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["blocked_by"], ["auth.users.id"], name=op.f("fk_users_blocked_by_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        schema="auth",
    )
    op.create_table(
        "permission_group_association",
        sa.Column("group_uuid", sa.Uuid(), nullable=False, comment="fk на группу"),
        sa.Column(
            "permission_uuid", sa.Uuid(), nullable=False, comment="fk на разрешение"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["group_uuid"],
            ["auth.groups.uuid"],
            name=op.f("fk_permission_group_association_group_uuid_groups"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_uuid"],
            ["auth.permissions.uuid"],
            name=op.f("fk_permission_group_association_permission_uuid_permissions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "group_uuid",
            "permission_uuid",
            name=op.f("pk_permission_group_association"),
        ),
        schema="auth",
    )
    op.create_index(
        op.f("ix_auth_permission_group_association_group_uuid"),
        "permission_group_association",
        ["group_uuid", "permission_uuid"],
        unique=False,
        schema="auth",
    )
    op.create_table(
        "role_group_association",
        sa.Column("role_uuid", sa.Uuid(), nullable=False, comment="fk роли"),
        sa.Column("group_uuid", sa.Uuid(), nullable=False, comment="fk группы"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["group_uuid"],
            ["auth.groups.uuid"],
            name=op.f("fk_role_group_association_group_uuid_groups"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_uuid"],
            ["auth.roles.uuid"],
            name=op.f("fk_role_group_association_role_uuid_roles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "role_uuid", "group_uuid", name=op.f("pk_role_group_association")
        ),
        schema="auth",
    )
    op.create_index(
        op.f("ix_auth_role_group_association_role_uuid"),
        "role_group_association",
        ["role_uuid", "group_uuid"],
        unique=False,
        schema="auth",
    )
    op.create_table(
        "session_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_uuid", sa.Uuid(), nullable=False),
        sa.Column("login_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("logout_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_count", sa.Integer(), nullable=False),
        sa.Column("device_info", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("session_jti", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_uuid"],
            ["auth.users.id"],
            name=op.f("fk_session_logs_user_uuid_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_logs")),
        schema="auth",
    )
    op.create_table(
        "user_access",
        sa.Column("user_uuid", sa.Uuid(), nullable=False, comment="fk пользователя"),
        sa.Column("role_uuid", sa.Uuid(), nullable=True, comment="fk роли"),
        sa.Column(
            "additional_permissions",
            sa.ARRAY(sa.UUID()),
            nullable=False,
            comment="дополнительные разрешения пользователя",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_uuid"],
            ["auth.roles.uuid"],
            name=op.f("fk_user_access_role_uuid_roles"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_uuid"],
            ["auth.users.id"],
            name=op.f("fk_user_access_user_uuid_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_uuid", name=op.f("pk_user_access")),
        schema="auth",
    )
    op.create_index(
        op.f("ix_auth_user_access_user_uuid"),
        "user_access",
        ["user_uuid", "role_uuid"],
        unique=False,
        schema="auth",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_auth_user_access_user_uuid"), table_name="user_access", schema="auth"
    )
    op.drop_table("user_access", schema="auth")
    op.drop_table("session_logs", schema="auth")
    op.drop_index(
        op.f("ix_auth_role_group_association_role_uuid"),
        table_name="role_group_association",
        schema="auth",
    )
    op.drop_table("role_group_association", schema="auth")
    op.drop_index(
        op.f("ix_auth_permission_group_association_group_uuid"),
        table_name="permission_group_association",
        schema="auth",
    )
    op.drop_table("permission_group_association", schema="auth")
    op.drop_table("users", schema="auth")
    op.drop_table("roles", schema="auth")
    op.drop_table("permissions", schema="auth")
    op.drop_table("groups", schema="auth")
