import logging
from ckan import authz, model

log = logging.getLogger(__name__)


def _requester_is_admin(context):
    """
    Check if the requester of an operation is an admin.

    Args:
    - context (dict): A dictionary containing contextual information for the request.

    Returns:
    - bool: True if the requester is an admin, False otherwise.
    """
    try:
        # Retrieve the user from the context.
        requester = context.get('user')
        # Check if the user has 'admin' permissions for any group.
        return _has_user_permission_for_some_group(requester, 'admin')
    except Exception as e:
        log.error(f"Error checking if requester is admin: {e}")
        return False


def _has_user_permission_for_some_group(user_name, permission):
    """
    Check if a user has a specific permission for any group.

    Args:
    - user_name (str): The username of the user.
    - permission (str): The permission to check for.

    Returns:
    - bool: True if the user has the given permission for any group, False otherwise.
    """
    try:
        # Get the user ID for the provided username.
        user_id = authz.get_user_id_for_username(user_name, allow_none=True)
        if not user_id:
            # If there's no user ID, the user does not exist, so return False.
            return False

        # Get all the roles associated with the given permission.
        roles = authz.get_roles_with_permission(permission)
        if not roles:
            # If there are no roles with the given permission, return False.
            return False

        # Check if the user has any of the roles associated with the given permission.
        member_exists = model.Session.query(model.Member) \
            .filter(model.Member.table_name == 'user') \
            .filter(model.Member.state == 'active') \
            .filter(model.Member.capacity.in_(roles)) \
            .filter(model.Member.table_id == user_id) \
            .exists()

        # If the user is not part of any group with the required roles, return False.
        if not model.Session.query(member_exists).scalar():
            return False

        # Check if there are active groups where the user has the required roles.
        group_exists = model.Session.query(model.Group) \
            .filter(model.Group.state == 'active') \
            .join(model.Member, model.Member.group_id == model.Group.id) \
            .filter(model.Member.table_id == user_id) \
            .filter(model.Member.capacity.in_(roles)) \
            .exists()

        return model.Session.query(group_exists).scalar()
    except Exception as e:
        log.error(f"Error checking user permission for group: {e}")
        return False
