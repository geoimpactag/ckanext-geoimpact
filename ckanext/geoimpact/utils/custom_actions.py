import ckan.plugins as p
from ckan.logic.action.get import organization_list as original_organization_list
from . import _requester_is_admin

def organization_list(context, data_dict):
    """
    Override CKAN's default method to retrieve a list of organizations.
    Administrators are allowed to retrieve the list of organizations.
    Non-administrators are only allowed to retrieve the list of organizations they are part of.
    """
    if _requester_is_admin(context):
        return original_organization_list(context, data_dict)
    user = context.get('auth_user_obj')
    if not user:
        return []
    user_orgs = p.toolkit.get_action('organization_list_for_user')({'user': user.id})
    return user_orgs