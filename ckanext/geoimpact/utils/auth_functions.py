import ckan.plugins as p
from ckan import authz, model
from ckan.common import asbool, _
from ckan.logic import auth as logic_auth, auth_allow_anonymous_access, NotFound
from . import _requester_is_admin


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


@auth_allow_anonymous_access
def organization_show(context, data_dict):
    """
    Override CKAN's default method to retrieve an organization.
    Only administrators or users within the organization are allowed to retrieve an organization.
    """
    if _requester_is_admin(context):
        return {'success': True}
    user = context.get('auth_user_obj')
    if not user:
        raise NotFound("Organization not found")
    user_orgs = p.toolkit.get_action('organization_list_for_user')({'user': user.id})
    org_id_or_name = data_dict.get('id')
    if any(org['id'] == org_id_or_name or org['name'] == org_id_or_name for org in user_orgs):
        return {'success': True}
    else:
        raise NotFound("Organization not found")
