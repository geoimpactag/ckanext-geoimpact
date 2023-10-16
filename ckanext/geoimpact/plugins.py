import logging
import ckan.plugins as p
import ckan.lib.mailer as mailer
from ckan.lib.plugins import DefaultTranslation
from ckan.common import _, CKANConfig

from .patches.emails import send_reset_link, send_invite
from .utils.auth_functions import organization_show, user_list, user_show, group_show
from .utils.custom_actions import organization_list
from .utils.template_helpers import (
    _get_valid_schemas,
    custom_get_facet_items_dict,
    get_available_schemas,
    get_fluent_label_from_schema,
    group_facet_items_by_label,
)

log = logging.getLogger(__name__)

QUERY_FIELDS = "name^4 title^4 tags^2 groups^2 extras_title_translated^4 extras_short_notes^2 text"

class GeoimpactPlugin(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.ITranslation)
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
            'organization_show': organization_show,
        }

    # IActions
    def get_actions(self):
        return {'organization_list': organization_list}

    def _log_data(self, text, data):
        log.error(f"{text}: {data}")


    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_available_schemas': get_available_schemas,
            'get_fluent_label_from_schema': get_fluent_label_from_schema,
            'group_facet_items_by_label': group_facet_items_by_label,
            'custom_get_facet_items_dict': custom_get_facet_items_dict,
            'log_data': self._log_data,
            'get_site_title': lambda: p.toolkit.config.get('ckan.site_title', ''),
        }

    # IPackageController
    def before_dataset_search(self, search_params):
        search_params['defType'] = 'edismax'
        try:
            # Append wildcard '*' to each word in the query string
            query_string = search_params.get('q', '')
            if query_string and not any(char in query_string for char in ':*"~'):
                words = query_string.split()
                wildcard_query = ' '.join(f"{word}*" for word in words)
                search_params['q'] = wildcard_query.strip()
                search_params['qf'] = QUERY_FIELDS
                
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
                    search_params['fq'] = search_params['fq'].replace(f'{field}:"', f'{field}:*"')

            return search_params
        except Exception as e:
            log.error(f"Error in before_dataset_search: {e}")
            return search_params

    def dataset_facets(self, facets_dict, package_type):
        facets_dict['data_providers'] = _('Data Providers')
        facets_dict['data_level'] = _('Data Level')
        facets_dict['functional_tags'] = _('Usability')
        return self._clean_facets(facets_dict)

    def _clean_facets(self, facets_dict):
        unwanted_keys = ['groups', 'license_id', 'res_format', 'organization']
        for key in unwanted_keys:
            facets_dict.pop(key, None)
        return facets_dict
