import json
import os.path
from flask import request
from ckan.lib.helpers import get_facet_items_dict
from ckan import plugins as p

# Initialize logging
import logging

log = logging.getLogger(__name__)

# Try importing yaml
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    log.warning("YAML library not found, .yaml and .yml files will not be supported.")


def _parse_schema_file(file_path):
    """Parse schema file based on its extension."""
    try:
        with open(file_path, 'r') as file:
            if file_path.endswith('.json'):
                return json.load(file)
            elif file_path.endswith(('.yaml', '.yml')) and YAML_AVAILABLE:
                return yaml.safe_load(file)
    except Exception as e:
        log.error(f"Error reading or parsing file {file_path}: {str(e)}")
    return None


def _get_valid_schemas():
    """Retrieve and parse valid schema files."""
    schemas_string = p.toolkit.config.get('scheming.dataset_schemas', '')
    schemas_list = [s.strip() for s in schemas_string.split() if s.strip()]

    valid_schemas = []
    for schema in schemas_list:
        module_name, file_path = schema.split(':')
        module = __import__(module_name, fromlist=[''])
        file_full_path = os.path.join(os.path.dirname(module.__file__), file_path)

        parsed_content = _parse_schema_file(file_full_path)
        if parsed_content and "dataset_type" in parsed_content:
            valid_schemas.append(parsed_content)

    return valid_schemas


def get_available_schemas():
    """Retrieve a list of available schemas with display names."""
    valid_schemas = _get_valid_schemas()
    return [
        {
            "name": schema["dataset_type"],
            "display_name": schema["dataset_type"].replace('_', ' ').title()
        }
        for schema in valid_schemas
    ]


def _get_choices_for_field(schemas, field_name):
    """Retrieve all choices for a given field name across all schemas."""
    for schema in schemas:
        for field in schema.get('dataset_fields', []):
            if field['field_name'] == field_name:
                return field.get('choices', [])
    return []


def get_fluent_label_from_schema(field_name, value):
    lang_code = p.toolkit.request.environ['CKAN_LANG']
    schemas = _get_valid_schemas()

    # Check if value is a string representation of a list
    if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass

    # Ensure values is a list, even if it's a single string
    values = value if isinstance(value, list) else [value]

    all_choices = _get_choices_for_field(schemas, field_name)
    labels = []
    for v in values:
        for choice in all_choices:
            if choice['value'] == v:
                labels.append(choice['label'].get(lang_code, v))
                break
        else:
            labels.append(v)  # Use the value if no label is found

    return set(labels)


def group_facet_items_by_label(items):
    current_data_providers = request.args.getlist('data_providers')
    current_labels = [get_fluent_label_from_schema('data_providers', data_provider) for data_provider in
                      current_data_providers]
    current_labels = [label for sublist in current_labels for label in sublist]

    grouped = {}
    for item in items:
        labels = get_fluent_label_from_schema('data_providers', item['name'])
        for label in labels:
            grouped.setdefault(label, {'name': label, 'count': 0, 'active': label in current_labels})
            grouped[label]['count'] += item['count']

    return list(grouped.values())


def group_choices_facet(facet, items, dataset_field):
    lang_code = p.toolkit.request.environ['CKAN_LANG'] or 'en'
    current_state_from_url = request.args.getlist(facet)  # list of strings to handle is_active
    choices = dataset_field.get('choices', [])

    grouped = {}
    for item in items:
        names = item['name']
        if isinstance(names, str) and names.startswith('[') and names.endswith(']'):
            try:
                names = json.loads(names)
            except json.JSONDecodeError:
                names = [names]
        else:
            names = [names]

        for name in names:
            for choice in choices:
                if choice['value'] == name:
                    label = choice['label'].get(lang_code, name)
                    grouped.setdefault(label, {'name': name, 'display_name': label, 'count': 0,
                                               'active': name in current_state_from_url})
                    grouped[label]['count'] += item['count']
                    break

    return list(grouped.values())


def custom_get_facet_items_dict(facet, search_facets=None, limit=None, exclude_active=False):
    items = get_facet_items_dict(facet, search_facets, limit, exclude_active)
    schema = _get_schema_for_facet(facet)
    if not schema:
        return sorted(items, key=lambda x: x['name'].lower())

    dataset_field = next((field for field in schema.get('dataset_fields', []) if field['field_name'] == facet), None)
    if not dataset_field:
        return sorted(items, key=lambda x: x['name'].lower())

    # this handles the case when schema has defined coices array
    if "label" in dataset_field and isinstance(dataset_field["label"], dict) and dataset_field.get('choices', []):
        return sorted(group_choices_facet(facet, items, dataset_field), key=lambda x: x['display_name'].lower())

    # this handles the case when schema is just translated text field
    if "label" in dataset_field and isinstance(dataset_field["label"], dict):
        return sorted(group_facet_items_by_label(items), key=lambda x: x['name'].lower())

    return sorted(items, key=lambda x: x['name'].lower())


def _get_schema_for_facet(facet):
    """Retrieve the schema file for a given facet."""
    schemas = _get_valid_schemas()
    for schema in schemas:
        for field in schema.get('dataset_fields', []):
            if field['field_name'] == facet:
                return schema
    return None
