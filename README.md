# Geoimpact CKAN Extension
## Overview
**Geoimpact** is a CKAN extension developed to augment our CKAN instance by introducing features oriented towards geospatial datasets. It leverages the robustness of [CKAN](https://ckan.org/), the world's leading open-source data portal platform, with specific features that are beneficial for users and organizations dealing with geo-specific datasets. For more details about geoimpact, please visit [geoimpact.ch](https://www.geoimpact.ch/).
### Features
1. **Custom Emails:** Enhanced email templates for user-related actions like password reset and invitations.
2. **Advanced Scheming:** Introduces custom presets and schemas to define the structure and behavior of datasets.
3. **Template Overriding:** Custom templates for dataset addition, and facet listing, as well as a customized footer.
4. **Utilities:** Special utility functions for authentication, actions, and templates.
## Technical Details
The geoimpact extension introduces several modifications and enhancements over the default CKAN functionalities. Below are the in-depth technical details of each part of the extension.
### Patches
- **emails.py:** This file overrides the default CKAN mailing functionalities. It introduces custom email templates for password reset and user invitation.
### Scheming
The scheming directory consists of presets and schemas:
- **presets/main_presets.json:** Contains custom presets, which are predefined configurations for CKAN fields.
- **schemas:** This directory houses schemas which define the structure of datasets:
  - **geoimpact_test.json:** A test schema for the geoimpact extension.
  - **main_schema.json:** The main schema used by geoimpact.
### Templates
- **emails:** Contains custom email templates for sending password reset links and user invitations.
- **scheming:** Houses display snippets and form snippets for custom field types.
- **snippets:** Contains templates for adding datasets and facet listing.
- **footer.html:** An overridden footer template for CKAN.
### Utilities
The utilities directory contains the core functionalities that the extension brings:
- **auth_functions.py:** Contains functions to override CKAN's default authorization checks.
- **custom_actions.py:** Provides custom actions for listing organizations.
- **template_helpers.py:** Contains helper functions used in Jinja2 templates.
### Translations
This section guides on how to manage translations in the geoimpact extension:
- **Updating Translations:** After updating the `.pot` file, update the `.po` files for each language using the command `python setup.py update_catalog -l [lang_code]`.
- **Compiling Translations:** Post updating the translations, compile them to generate the respective `.mo` files using the command `python setup.py compile_catalog -l [lang_code]`.
### Main
- **plugins.py:** The main plugin file which declares the geoimpact extension and its functionalities.
### Presets
- **presets.json:** Global presets file.
---
## Support
For any issues or concerns related to the geoimpact CKAN Extension, please reach out to our support team at support@geoimpact.ch.