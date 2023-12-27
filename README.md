# Geoimpact CKAN Extension

## Overview
This extension shifts the focus of CKAN from the download portal to the multilingual metadata catalog of a data-driven company. 
It leverages the robustness of [CKAN](https://ckan.org/), the world's leading open-source data portal platform, 
with specific features that are beneficial for organizations that want to maintain their own 
datacatalog and share it with their customers. 
For more details about geoimpact, please visit [geoimpact.ch](https://www.geoimpact.ch/).

### Features
1. **Custom Emails:** Enhanced email templates for user-related actions like password reset and invitations.
2. **Advanced Scheming:** Introduces custom presets and schemas to define the structure and behavior of datasets.
3. **Template Overriding:** Custom templates for dataset addition, and facet listing, as well as a customized footer.
4. **Utilities:** Special utility functions for authentication, actions, and templates.
5. **Translated Facet Values:** The extension offers the capability to display translated facet values. This is achieved by defining the `used_in_facets` attribute in the schema for fields that have `choices`. If the `choices` attribute is present, the extension will display translated versions of these `choices` based on the current language setting. If `choices` is not defined for a field marked with `used_in_facets`, the extension will display the field's value instead of its translated version.

## Technical Details

### Extensions
We use the following extensions: 

- activity
- scheming_datasets
- fluent
- geoimpact

### Patches
- **emails.py:** This file overrides the default CKAN mailing functionalities. It introduces custom email templates for password reset and user invitation.

### Scheming
Our schemas are inspired by following sources:
- https://github.com/ckan/ckanext-scheming/tree/master/ckanext/scheming
- https://github.com/ckan/ckanext-fluent/tree/master/ckanext/fluent
- https://github.com/opendata-swiss/ckanext-switzerland-ng/tree/master/ckanext/switzerland

The scheming directory consists of presets and schemas:
- **presets/main_presets.json:** Contains custom presets, which are predefined configurations for CKAN fields.
- **schemas:** This directory houses schemas which define the structure of datasets:
  - **geoimpact_test.json:** A test schema for the geoimpact extension.
  - **main_schema.json:** The main schema used by geoimpact.

### Templates
- **emails:** Contains custom email templates for sending password reset links and user invitations.
- **scheming:** Houses display snippets and form snippets for custom field types.
  - display_snippets:
    - geoimpact_fluent_tags.html: TODO: autocomplete for fluent tags - not used yet
    - geoimpact_multiple_choice_url.html: Add html links with additional url parameter to multiple choice displays.
- **snippets:** 
  - add_dataset.html: Overriding add datasets button.
  - facet_list.html: Overriding facet listing (filter section).
  - package_item.html: Add translation to listed packages (dataset overview).
- **header.html:** An overridden header (i.e., navigation menu) template for CKAN.
- **footer.html:** An overridden footer template for CKAN.

### Utilities
The utilities directory contains the core functionalities that the extension brings:
- **auth_functions.py:** Contains functions to override CKAN's default authorization checks.
  - Users (except sysadmin) cannot see other users
  - Users (except sysadmin) cannot see other organizations
  - Inspired by: https://github.com/qld-gov-au/ckanext-qgov
- **custom_actions.py:** Provides custom actions for listing organizations.
- **template_helpers.py:** Contains helper functions used in Jinja2 templates.

### Translations
This section guides on how to manage translations in the geoimpact extension:
- **Extracting new translation strings:** If you have added new translation strings, you need to extract them to the `*.pot` file. You can do this by running `python setup.py extract_messages`. For more information about extracting the string, see [Extract strings](https://docs.ckan.org/en/2.10/extensions/translating-extensions.html?highlight=extract_messages#extract-strings).
- **Updating Translations:** After updating the `.pot` file, update the `.po` files for each language using the command `python setup.py update_catalog -l [lang_code]`.
- **Compiling Translations:** Post updating the translations, compile them to generate the respective `.mo` files using the command `python setup.py compile_catalog -l [lang_code]`.

### Main
- **plugins.py:** The main plugin file which declares the geoimpact extension and its functionalities.

### Presets
- **presets.json:** Global presets file.

## Installation
This section describes the steps to install and configure CKAN and extensions.

### Prerequisites
CKAN requires the packages libpq5, Redis, nginx, supervisor as well as Solr. 
PostgreSQL is required for the datastore, but we use an existing instance.

#### Create PostgreSQL DB, schema and user
Note: Originally we tried to use a dedicated schema for CKAN named "ckan". 
But it turned out that a few specific DB queries are hardcoded to use the public schema.
```
-- create DB
CREATE DATABASE datacat;

-- switch to new DB and enable PostGIS
CREATE EXTENSION postgis;

-- create user and user's schema
CREATE USER ckan WITH PASSWORD '<password>';
GRANT CONNECT ON DATABASE datacat TO ckan;

-- https://postgis.net/workshops/postgis-intro/schemas.html
-- CREATE SCHEMA ckan authorization ckan;

-- set default schema
-- ALTER USER ckan SET search_path TO ckan;

-- grant ckan full permission on public schema
GRANT ALL ON SCHEMA public TO ckan;
GRANT ALL ON ALL TABLES IN SCHEMA public TO ckan;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO ckan;

-- grant same permissions for future tables in schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES TO ckan;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO ckan;
```

#### Install dependencies (packages)
Update Ubuntu’s package index:
```
sudo apt update
```
Install the Ubuntu packages that CKAN requires (and ‘git’, to enable you to install CKAN extensions):
```
sudo apt install -y libpq5 redis-server nginx supervisor
```

#### Install dependencies (Solr)
Install the OS dependencies:
```
sudo apt-get install openjdk-8-jdk
```
Download the latest supported version from the Solr downloads page. CKAN supports Solr version 8.x. Extract the install script file to your desired location (adjust the Solr version number to the one you are using):
```
tar xzf solr-8.11.2.tgz solr-8.11.2/bin/install_solr_service.sh --strip-components=2
```
Run the installation script as root:
```
sudo bash ./install_solr_service.sh solr-8.11.2.tgz
```
Check that Solr started running:
```
sudo service solr status
```
Create a new core for CKAN:
```
sudo -u solr /opt/solr/bin/solr create -c ckan
```
Replace the standard schema with the CKAN one:
```
sudo -u solr wget -O /var/solr/data/ckan/conf/managed-schema https://raw.githubusercontent.com/geoimpactag/ckanext-geoimpact/main/solr/schema.xml
```
Restart Solr:
```
sudo service solr restart
```

### CKAN installation

#### Install CKAN base
Download the CKAN package (on Ubuntu 22.04):
```
wget https://packaging.ckan.org/python-ckan_2.10-jammy_amd64.deb
```
Install the CKAN package (on Ubuntu 22.04):
```
sudo dpkg -i python-ckan_2.10-jammy_amd64.deb
```

#### Install CKAN extensions
Required extensions:
- https://github.com/ckan/ckanext-scheming (installed with ckanext-fluent)
- https://github.com/ckan/ckanext-fluent
- https://github.com/geoimpactag/ckanext-geoimpact

Perform the following procedure first for ckanext-fluent, then for ckanext-geoimpact:
```
sudo su
. /usr/lib/ckan/default/bin/activate
cd /usr/lib/ckan/default/src/
git clone https://github.com/ckan/ckanext-fluent.git
cd ckanext-fluent
python setup.py develop
pip install -r requirements.txt
exit
```
Overwrite `ckanext-scheming` extencion template to hide the description of package
```
cd /usr/lib/ckan/default/src/ckanext-scheming/ckanext/scheming/templates/scheming/package/snippets/
nano additional_info.html
```
Add `notes_translated` to excluded `exclude_fields`
```
{%- set exclude_fields = [
    'id',
    'title',
    'name',
    'notes',
    'notes_translated',
    'tag_string',
    'license_id',
    'owner_org',
    ] -%}
```

#### Set up a writable directory
Create the directory where CKAN will be able to write files:
```
sudo mkdir -p /var/lib/ckan/default
```
Set the permissions of this directory. The Nginx’s user (www-data) must have read, write and execute permissions on it:
```
sudo chown www-data /var/lib/ckan/default
sudo chmod u+rwx /var/lib/ckan/default
```

### First startup
Reload the Supervisor daemon so the new processes are picked up:
```
sudo supervisorctl reload
```
After a few seconds run the following command to check the status of the processes:
```
sudo supervisorctl status
```
You should see three processes running without errors:
```
ckan-datapusher:ckan-datapusher-00   RUNNING   pid 1963, uptime 0:00:12
ckan-uwsgi:ckan-uwsgi-00             RUNNING   pid 1964, uptime 0:00:12
ckan-worker:ckan-worker-00           RUNNING   pid 1965, uptime 0:00:12
```

### Error Logs
If some processes reports an error, make sure you’ve run all the previous steps and check the 
logs located in: ```/var/log/ckan```.

Application errors are usually logged in the file: ``/var/log/ckan/ckan-uwsgi.stderr.log``.

Startup errors are usually logged in the file: ``/var/log/ckan/ckan-worker.stderr.log``

### Redeployment
Changes to the geoimpact extension can be deployed as follows:
````
cd /usr/lib/ckan/default/src/ckanext-geoimpact
git pull
sudo supervisorctl restart all
````

---
## Support
For any issues or concerns related to the geoimpact CKAN Extension, please reach out to our support team at support@geoimpact.ch.
