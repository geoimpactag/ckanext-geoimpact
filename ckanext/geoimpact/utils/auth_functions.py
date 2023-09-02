from ckan import authz, model
from ckan.common import asbool, _
from ckan.logic import auth as logic_auth, auth_allow_anonymous_access


def user_list(context, data_dict):
    """
    Override CKAN's default method to retrieve a list of users.
    Only administrators are allowed to retrieve this list.

    Args:
    - context (dict): A dictionary containing contextual information for the request.
    - data_dict (dict): A dictionary containing data needed for the operation.

    Returns:
    - dict: A dictionary indicating if the operation was successful.
    """
    # Check if the requester is an admin.
    # If they are, success is set to True, allowing them to retrieve the list of users.
    return {'success': _requester_is_admin(context)}


@auth_allow_anonymous_access
def user_show(context, data_dict):
    """
    Override CKAN's default method to retrieve a user.
    Only administrators and the user themselves are allowed to retrieve a user.

    Args:
    - context (dict): A dictionary containing contextual information for the request.
    - data_dict (dict): A dictionary containing data needed for the operation.

    Returns:
    - dict: A dictionary indicating if the operation was successful.
    """
    if _requester_is_admin(context):
        return {'success': True}
    requester = context.get('user')
    user_id = data_dict.get('id', None)
    if id:
        user_obj = model.User.get(user_id)
    else:
        user_obj = data_dict.get('user_obj', None)
    if user_obj:
        return {'success': requester in [user_obj.name, user_obj.id]}

    return {'success': False}


@auth_allow_anonymous_access
def group_show(context, data_dict):
    """
    Override CKAN's default method to retrieve a group.
    Only administrators and users with the 'update' permission for the group are allowed to retrieve a group.

    Args:
    - context (dict): A dictionary containing contextual information for the request.
    - data_dict (dict): A dictionary containing data needed for the operation.

    Returns:
    - dict: A dictionary indicating if the operation was successful.
    """
    user = context.get('user')
    group = logic_auth.get_group_object(context, data_dict)
    if group.state == 'active' and \
            not asbool(data_dict.get('include_users', False)) and \
            data_dict.get('object_type', None) != 'user':
        return {'success': True}
    authorized = authz.has_user_permission_for_group_or_org(
        group.id, user, 'update')
    if authorized:
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User %s not authorized to read group %s') % (user, group.id)}


def _requester_is_admin(context):
    """
    Check if the requester of an operation is an admin.

    Args:
    - context (dict): A dictionary containing contextual information for the request.

    Returns:
    - bool: True if the requester is an admin, False otherwise.
    """
    # Retrieve the user from the context.
    requester = context.get('user')
    # Check if the user has 'admin' permissions for any group.
    return _has_user_permission_for_some_group(requester, 'admin')


def _has_user_permission_for_some_group(user_name, permission):
    """
    Check if a user has a specific permission for any group.

    Args:
    - user_name (str): The username of the user.
    - permission (str): The permission to check for.

    Returns:
    - bool: True if the user has the given permission for any group, False otherwise.
    """
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

    # Query the database to check if the user has any of the roles associated with the given permission.
    q = model.Session.query(model.Member) \
        .filter(model.Member.table_name == 'user') \
        .filter(model.Member.state == 'active') \
        .filter(model.Member.capacity.in_(roles)) \
        .filter(model.Member.table_id == user_id)

    # Extract group IDs for which the user has the required roles.
    group_ids = [row.group_id for row in q.all()]

    if not group_ids:
        # If the user is not part of any group with the required roles, return False.
        return False

    # Query the database to check if the groups are active.
    q = model.Session.query(model.Group) \
        .filter(model.Group.state == 'active') \
        .filter(model.Group.id.in_(group_ids))

    # Return True if there are active groups where the user has the required roles, otherwise return False.
    return bool(q.count())