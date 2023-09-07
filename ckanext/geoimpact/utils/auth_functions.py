import logging
import ckan.plugins as p
from ckan import authz, model
from ckan.common import asbool, _
from ckan.logic import auth as logic_auth, auth_allow_anonymous_access, NotFound
from . import _requester_is_sysadmin

log = logging.getLogger(__name__)


def user_list(context, data_dict):
    """Only sysadministrators are allowed to retrieve the list of users."""
    return {'success': _requester_is_sysadmin(context)}


@auth_allow_anonymous_access
def user_show(context, data_dict):
    """
    Determines permission to retrieve user details.
    
    Allows retrieval in the following scenarios:
    - The requester is a sysadmin.
    - The requester is trying to access their own details.
    - The requester is an admin in an organization that the target user is a member of.

    Raises NotFound error if a non-sysadmin user tries to access sysadmin user details.

    :param context: Dictionary with context data.
    :param data_dict: Dictionary with data needed to check permission (must include 'id' or 'user_obj').
    :return: Dictionary with success key and a boolean value indicating if the retrieval is allowed.
    """
    
    # Grant permission to sysadmins for retrieving any user details
    if _requester_is_sysadmin(context):
        return {'success': True}

    # Get requester username and target user details from data_dict
    requester = context.get('user')
    user_id = data_dict.get('id', None)
    user_obj = model.User.get(user_id) if user_id else data_dict.get('user_obj', None)

    # Restrict access to sysadmin user details for non-sysadmin users
    if user_obj and user_obj.sysadmin:
        raise NotFound("User not found")

    # Grant permission for users to access their own details
    if user_obj and requester in [user_obj.name, user_obj.id]:
        return {'success': True}

    # Retrieve the list of organizations where the requester is an admin
    requester_orgs = p.toolkit.get_action('organization_list_for_user')({'user': requester})

    # Ensure user_obj is not None before fetching the list of organizations the target user is a member of
    if user_obj:
        user_orgs = p.toolkit.get_action('organization_list_for_user')({'user': user_obj.id})
    else:
        return {'success': False}

    # Extract organization IDs for requester (as admin) and the target user
    requester_org_ids = [org['id'] for org in requester_orgs if org.get('capacity') == 'admin']
    user_org_ids = [org['id'] for org in user_orgs]

    # Grant permission if there is a common organization where the requester is an admin and the target user is a member
    if set(requester_org_ids) & set(user_org_ids):
        return {'success': True}
    
    # Deny access if none of the above conditions are met
    return {'success': False}


@auth_allow_anonymous_access
def group_show(context, data_dict):
    """Only administrators and users with the 'update' permission for the group are allowed to retrieve a group."""
    user = context.get('user')
    group = logic_auth.get_group_object(context, data_dict)

    if group.state == 'active' and not asbool(data_dict.get('include_users', False)) and data_dict.get('object_type',
                                                                                                       None) != 'user':
        return {'success': True}

    if authz.has_user_permission_for_group_or_org(group.id, user, 'update'):
        return {'success': True}
    else:
        return {'success': False, 'msg': _('User %s not authorized to read group %s') % (user, group.id)}


@auth_allow_anonymous_access
def organization_show(context, data_dict):
    """
    Determines permission to retrieve organization details.
    
    Allows retrieval in the following scenarios:
    - The requester is a sysadmin.
    - The requester is a member of the target organization (irrespective of their role in the organization).

    Raises NotFound error if the target organization does not exist or if the requester is not allowed to view the details.

    :param context: Dictionary with context data.
    :param data_dict: Dictionary with data needed to check permission (must include 'id' representing organization ID or name).
    :return: Dictionary with success key and a boolean value indicating if the retrieval is allowed.
    """
    
    # Get authenticated user object from the context
    user = context.get('auth_user_obj')
    if not user:
        raise NotFound("Organization not found")
    
    # Grant permission to sysadmins for retrieving any organization details
    if _requester_is_sysadmin(context):
        return {'success': True}

    # Retrieve the list of organizations the user is a member of (including organizations where they are admin or editor)
    user_orgs = p.toolkit.get_action('organization_list_for_user')({'user': user.id})
    org_id_or_name = data_dict.get('id')

    # Grant permission if the user is a member of the target organization (checked by ID or name)
    if any(org['id'] == org_id_or_name or org['name'] == org_id_or_name for org in user_orgs):
        return {'success': True}
    else:
        raise NotFound("Organization not found")
