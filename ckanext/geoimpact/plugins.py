import ckan.plugins as p
import ckan.lib.mailer as mailer
# from ckan.common import CKANConfig
# from ckan.plugins import IAuthFunctions, toolkit
from ckan.common import _, CKANConfig

from .patches.emails import send_reset_link, send_invite
from .utils.auth_functions import organization_show, user_list, user_show, group_show
from .utils.custom_actions import organization_list
from .utils.template_helpers import get_available_schemas, get_fluent_label_from_schema, get_fluent_value_from_label, \
    group_facet_items_by_label


class GeoimpactPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IAuthFunctions, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    # Monkey patches for emails to use custom templates
    mailer.send_reset_link = send_reset_link
    mailer.send_invite = send_invite

    # Helper functions
    def get_helpers(self):
        return {
            'get_available_schemas': get_available_schemas,
            'get_fluent_label_from_schema': get_fluent_label_from_schema,
            'get_fluent_value_from_label': get_fluent_value_from_label,
            'group_facet_items_by_label': group_facet_items_by_label,
            'print_template_value': lambda x: log('Template Var: ', x),
        }

    # IActions
    def get_actions(self):
        return {
            'organization_list': organization_list,
        }

    # IPackageController
    def before_dataset_search(self, search_params):
        """
        This function is called by ckan before a search is executed
        We overwrite the default search here
        """
        filter_query = search_params.get('fq', '')
        # Check if 'categories' parameter is present
        if filter_query and 'categories:' in filter_query:
            # Replace the filter query to include wildcards for a broader match
            search_params['fq'] = search_params['fq'].replace('categories:"', 'categories:*"').replace('"', '"*')

        return search_params

    # IConfigurer
    def update_config(self, config: CKANConfig):
        """
        This function is called by ckan to update the config
        We overwrite the default config here
        """
        p.toolkit.add_template_directory(config, 'templates')

        return config

    # IAuthFunctions
    def get_auth_functions(self):
        """
        This function is called by ckan to get the auth functions
        We overwrite the default auth functions here
        """
        auth_functions = {
            'user_list': user_list,
            'user_show': user_show,
            'group_show': group_show,
            'organization_show': organization_show,
        }

        return auth_functions

    # IFacets
    def _facets(self, facets_dict):
        """
        Remove "Groups", ... from facets, see: https://github.com/okfn/ckanext-hidegroups/blob/master/ckanext/hidegroups/plugin.py
        """
        if 'groups' in facets_dict:
            del facets_dict['groups']
        if 'license_id' in facets_dict:
            del facets_dict['license_id']
        if 'res_format' in facets_dict:
            del facets_dict['res_format']
        if 'organization' in facets_dict:
            del facets_dict['organization']
        return facets_dict

    def dataset_facets(self, facets_dict, package_type):
        """
        This function is called by ckan to get the dataset facets.
        We overwrite the default dataset facets here
        """
        facets_dict['categories'] = _('Categories')
        return self._facets(facets_dict)

    def group_facets(self, facets_dict, group_type, package_type):
        """
        This function is called by ckan to get the group facets.
        We overwrite the default dataset facets here
        """
        return self._facets(facets_dict)

    def organization_facets(self, facets_dict, organization_type, package_type):
        """
        This function is called by ckan to get the organization facets.
        We overwrite the default dataset facets here
        """
        return self._facets(facets_dict)

