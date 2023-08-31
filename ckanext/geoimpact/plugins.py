from ckan import plugins as p
import ckan.lib.mailer as mailer
from ckan.common import CKANConfig
from ckan.plugins import IAuthFunctions, toolkit

from .patches import send_reset_link
from .utils.auth_functions import user_list


class GeoimpactPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(IAuthFunctions, inherit=True)

    mailer.send_reset_link = send_reset_link

    # IConfigurer
    def update_config(self, config: CKANConfig):
        """
        This function is called by ckan to update the config
        We overwrite the default config here
        """
        toolkit.add_template_directory(config, 'templates')

        return config

    # IAuthFunctions
    def get_auth_functions(self):
        """
        This function is called by ckan to get the auth functions
        We overwrite the default auth functions here
        """
        auth_functions = {
            'user_list': user_list,
        }

        return auth_functions
