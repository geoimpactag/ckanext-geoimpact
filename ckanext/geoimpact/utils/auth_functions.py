import logging
import ckan.plugins as p
from ckan import authz, model
from ckan.common import asbool, _
from ckan.logic import auth as logic_auth, auth_allow_anonymous_access, NotFound
from . import _requester_is_admin

log = logging.getLogger(__name__)


def user_list(context, data_dict):
    """Only administrators are allowed to retrieve the list of users."""
    return {'success': _requester_is_admin(context)}


@auth_allow_anonymous_access
def user_show(context, data_dict):
    """Only administrators and the user themselves are allowed to retrieve a user."""
    if _requester_is_admin(context):
        return {'success': True}

    requester = context.get('user')
    user_id = data_dict.get('id', None)
    user_obj = model.User.get(user_id) if user_id else data_dict.get('user_obj', None)

    if user_obj and requester in [user_obj.name, user_obj.id]:
        return {'success': True}
    else:
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
    """Only administrators or users within the organization are allowed to retrieve an organization."""
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
