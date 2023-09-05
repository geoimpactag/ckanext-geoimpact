import json
import os.path
from flask import request
from ckan import model
from ckan import plugins as p

# Try importing yaml, and set a flag if successful
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def _get_valid_schemas():
    """
    Returns a list of valid schemas
    """
    # Fetch the scheming.dataset_schemas configuration value
    schemas_string = p.toolkit.config.get('scheming.dataset_schemas', '')

    # Split the string by newlines or spaces to get individual schema paths
    schemas_list = [s.strip() for s in schemas_string.split() if s.strip()]

    # Iterate over each schema path and parse the content
    valid_schemas = []
    for schema in schemas_list:
        # Extracting the module and file path
        module_name, file_path = schema.split(':')
        module = __import__(module_name, fromlist=[''])
        file_full_path = os.path.join(os.path.dirname(module.__file__), file_path)

        # Read and parse the file based on its extension
        with open(file_full_path, 'r') as file:
            if file_path.endswith('.json'):
                parsed_content = json.load(file)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                if not YAML_AVAILABLE:
                    # If YAML is not available, log a warning and skip this schema
                    p.toolkit.log.warning(f"Failed to parse {file_path} as YAML is not available.")
                    continue
                parsed_content = yaml.safe_load(file)
            else:
                # Skip if the file is neither JSON nor YAML
                continue

        # Check if the parsed content has the 'dataset_type' key
        if "dataset_type" in parsed_content and isinstance(parsed_content["dataset_type"], str):
            valid_schemas.append(parsed_content)

    return valid_schemas


def get_available_schemas():
    """
    Returns a list of available schemas
    """
    valid_schemas = _get_valid_schemas()

    # Convert the list of valid schemas to a list of dictionaries with name and display_name.
    return [
        {
            "name": schema["dataset_type"],
            "display_name": schema["dataset_type"].replace('_', ' ').title()
        }
        for schema in valid_schemas
    ]


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

    result_labels = []

    for v in values:
        label_found = False
        for schema in schemas:
            for field in schema.get('dataset_fields', []):
                if field['field_name'] == field_name:
                    for choice in field.get('choices', []):
                        if choice['value'] == v:
                            result_labels.append(choice['label'].get(lang_code, v))
                            label_found = True
                            break  # exit the inner loop once label is found
                    if label_found:
                        break  # exit the outer loop once label is found

        # If label is not found for this value, append the value itself
        if not label_found:
            result_labels.append(v)

    return set(result_labels)


def get_fluent_value_from_label(field_name, label):
    lang_code = p.toolkit.request.environ['CKAN_LANG']
    schemas = _get_valid_schemas()

    for schema in schemas:
        for field in schema.get('dataset_fields', []):
            if field['field_name'] == field_name:
                for choice in field.get('choices', []):
                    if choice['label'].get(lang_code) == label:
                        return choice['value']

    return None


def group_facet_items_by_label(items):

    # Get the current categories from the URL
    current_categories = request.args.getlist('categories')
    current_labels = [get_fluent_label_from_schema('categories', category) for category in current_categories]
    # Flatten the list of lists into a single list
    current_labels = [label for sublist in current_labels for label in sublist]

    grouped = {}
    for item in items:
        labels = get_fluent_label_from_schema('categories', item['name'])
        for label in labels:
            if label in grouped:
                grouped[label]['count'] += item['count']
            else:
                # Check if label is currently active
                is_active = label in current_labels
                grouped[label] = {
                    'name': label,
                    'count': item['count'],
                    'active': is_active
                }
    return list(grouped.values())