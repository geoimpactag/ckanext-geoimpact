import logging
import ckan.plugins as p
from ckan.logic.action.get import organization_list as original_organization_list
from . import _requester_is_sysadmin

log = logging.getLogger(__name__)


def organization_list(context, data_dict):
    """
    Override CKAN's default method to retrieve a list of organizations.
    Administrators are allowed to retrieve the list of organizations.
    Non-administrators are only allowed to retrieve the list of organizations they are part of.
    """
    try:
        # If the requester is an admin, return the original list of organizations.
        if _requester_is_sysadmin(context):
            return original_organization_list(context, data_dict)

        # For non-admin users, only return organizations they are part of.
        user = context.get('auth_user_obj')
        if not user:
            return []

        user_orgs = p.toolkit.get_action('organization_list_for_user')(context, {'include_dataset_count': True})
        return user_orgs

    except Exception as e:
        log.error(f"Error retrieving organization list: {str(e)}")
        return []
