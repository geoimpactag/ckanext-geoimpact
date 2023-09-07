import logging
import ckan.plugins as p
import ckan.lib.mailer as mailer
from ckan.common import _, CKANConfig

from .patches.emails import send_reset_link, send_invite
from .utils.auth_functions import organization_show, user_list, user_show, group_show
from .utils.custom_actions import organization_list
from .utils.template_helpers import (
    _get_valid_schemas,
    custom_get_facet_items_dict,
    get_available_schemas,
    get_fluent_label_from_schema,
    group_facet_items_by_label
)

log = logging.getLogger(__name__)


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

    # IConfigurer
    def update_config(self, config: CKANConfig):
        p.toolkit.add_template_directory(config, 'templates')
        return config

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'user_list': user_list,
            'user_show': user_show,
            'group_show': group_show,
            'organization_show': organization_show,
        }

    # IActions
    def get_actions(self):
        return {'organization_list': organization_list}

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_available_schemas': get_available_schemas,
            'get_fluent_label_from_schema': get_fluent_label_from_schema,
            'group_facet_items_by_label': group_facet_items_by_label,
            'custom_get_facet_items_dict': custom_get_facet_items_dict,
        }

    # IPackageController
    def before_dataset_search(self, search_params):
        try:
            filter_query = search_params.get('fq', '')

            # Get the valid schemas
            schemas = _get_valid_schemas()

            # Identify fields that allow multiple selections
            multi_value_fields = []
            for schema in schemas:
                for field in schema.get('dataset_fields', []):
                    if "choices" in field and isinstance(field["choices"], list) and len(field["choices"]) > 1:
                        multi_value_fields.append(field['field_name'])

            # Check if filter_query contains any of the multi_value_fields
            for field in multi_value_fields:
                if f"{field}:" in filter_query:
                    log.info(f"Original search params for {field}: {search_params['fq']}")
                    search_params['fq'] = search_params['fq'].replace(f'{field}:"', f'{field}:*"')
                    log.info(f"Modified search params for {field}: {search_params['fq']}")

            return search_params
        except Exception as e:
            log.error(f"Error in before_dataset_search: {e}")
            return search_params

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
        facets_dict['data_providers'] = _('Data Providers')
        facets_dict['data_level'] = _('Data Level')
        return self._clean_facets(facets_dict)

    def group_facets(self, facets_dict, group_type, package_type):
        return self._facets(facets_dict)

    def organization_facets(self, facets_dict, organization_type, package_type):
        return self._clean_facets(facets_dict)

    def _clean_facets(self, facets_dict):
        unwanted_keys = ['groups', 'license_id', 'res_format', 'organization']
        for key in unwanted_keys:
            facets_dict.pop(key, None)
        return facets_dict
