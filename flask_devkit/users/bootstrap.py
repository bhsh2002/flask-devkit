# flask_devkit/users/bootstrap.py

from sqlalchemy.orm import Session

from flask_devkit.users.models import (
    Permission,
    Role,
    User,
    UserRoleAssociation,
)

DEFAULT_PERMISSIONS: list[str] = [
    # User management
    "create:user",
    "read:user",
    "update:user",
    "delete:user",
    # Role management
    "create:role",
    "read:role",
    "update:role",
    "delete:role",
    # Permission management
    "create:permission",
    "read:permission",
    "update:permission",
    "delete:permission",
    # Admin actions
    "assign_role:user",
    "revoke_role:user",
    "read_roles:user",
    "assign_permission:role",
    "revoke_permission:role",
    "read_permissions:role",
]


def _get_or_create_permission(session: Session, name: str) -> Permission:
    perm = session.query(Permission).filter(Permission.name == name).first()
    if perm is None:
        perm = Permission(name=name)
        session.add(perm)
        session.flush()
    return perm


def _get_or_create_role(
    session: Session, name: str, display_name: str, is_system_role: bool = False
) -> Role:
    role = session.query(Role).filter(Role.name == name).first()
    if role is None:
        role = Role(name=name, display_name=display_name, is_system_role=is_system_role)
        session.add(role)
        session.flush()
    return role


def seed_default_auth(
    session: Session, *, admin_username: str, admin_password: str
) -> dict:
    """
    Idempotently seed default permissions, an 'admin' role with full permissions,
    and an initial admin user assigned to that role.
    """
    # Fetch existing permissions in one query to avoid N+1 problem
    existing_perms_query = session.query(Permission).filter(
        Permission.name.in_(DEFAULT_PERMISSIONS)
    )
    existing_perms_map = {p.name: p for p in existing_perms_query}

    created_perms = 0
    perms: list[Permission] = []
    for name in DEFAULT_PERMISSIONS:
        perm = existing_perms_map.get(name)
        if perm is None:
            perm = Permission(name=name)
            session.add(perm)
            created_perms += 1
        perms.append(perm)

    # Flush to get instances ready for association
    session.flush()

    admin_role = _get_or_create_role(
        session, name="admin", display_name="Administrator", is_system_role=True
    )

    current_perm_names = {p.name for p in (admin_role.permissions or [])}
    for perm in perms:
        if perm.name not in current_perm_names:
            admin_role.permissions.append(perm)

    admin_user = session.query(User).filter(User.username == admin_username).first()
    created_user = False
    if admin_user is None:
        admin_user = User(username=admin_username)
        admin_user.set_password(admin_password)
        session.add(admin_user)
        created_user = True
        session.flush()  # Flush to get the admin_user.id before association
    else:
        # If user exists, just update the password to the provided one
        admin_user.set_password(admin_password)
        session.add(admin_user)

    # Check if the role is already assigned to the user
    existing_association = (
        session.query(UserRoleAssociation)
        .filter_by(user_id=admin_user.id, role_id=admin_role.id)
        .first()
    )
    if not existing_association:
        association = UserRoleAssociation(user_id=admin_user.id, role_id=admin_role.id)
        session.add(association)

    session.commit()

    return {
        "created_permissions": created_perms,
        "created_admin_user": created_user,
        "admin_role_id": admin_role.id,
        "admin_username": admin_username,
    }
