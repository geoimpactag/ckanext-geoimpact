import json
import os.path
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
