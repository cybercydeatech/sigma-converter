import os
import logging
from ruamel.yaml import YAML

# Constants
RULES_DIR = '/home/rafiq/cydea/repos/sigma-converter/elastalert_rules/'

def modify_elastalert_rules():
    """Modify ElastAlert rules by applying necessary changes and maintaining the original folder structure."""
    yaml = YAML()
    
    for root, _, files in os.walk(RULES_DIR):
        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                elastalert_rule = os.path.join(root, file)
                
                logging.info(f"Processing rule file: {elastalert_rule}")
                
                # Read the content of the ElastAlert rule
                with open(elastalert_rule, 'r') as f:
                    content = f.read()
                
                # If the file is empty, delete it
                if not content.strip():
                    os.remove(elastalert_rule)
                    logging.info(f"Deleted empty rule file: {elastalert_rule}")
                    continue
                
                # Load the content as YAML
                try:
                    data = yaml.load(content)
                except Exception as e:
                    logging.error(f"Error loading YAML content from {elastalert_rule}: {e}")
                    continue
                
                # Update the "name" field based on the filename without extension
                rule_name = os.path.splitext(file)[0]
                data['name'] = rule_name
                
                # Add "is_enabled: false" if not present
                if 'is_enabled' not in data:
                    data['is_enabled'] = False
                
                # Save the modified rule with a .yaml extension
                modified_rule_path = os.path.join(root, f"{rule_name}.yaml")
                try:
                    with open(modified_rule_path, 'w') as f:
                        yaml.dump(data, f)
                    logging.info(f"Saved modified rule to {modified_rule_path}")
                except Exception as e:
                    logging.error(f"Error saving modified rule to {modified_rule_path}: {e}")
                
                # Remove the original file if it's not the modified file
                if elastalert_rule != modified_rule_path and os.path.exists(elastalert_rule):
                    os.remove(elastalert_rule)
                    logging.info(f"Removed original rule file: {elastalert_rule}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Call the function to modify ElastAlert rules
    modify_elastalert_rules()
