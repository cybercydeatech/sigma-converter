import os
import subprocess
import logging
import shutil
import time
from datetime import datetime
import ruamel.yaml
from ruamel.yaml import YAML
import yaml

# Configuration
SIGMA_REPO_URL = 'https://github.com/SigmaHQ/sigma.git'
SIGMA_REPO_DIR = 'sigma_repo'
ELASTALERT_RULES_DIR = 'sigma_elastalert_rules'
MODIFIED_RULES_DIR = 'modified_rules'
ENABLE_ELASTALERT_CONVERSION = True  # Set this to False to disable ElastAlert conversion
UPDATE_INTERVAL_HOURS = 24  # Update interval in hours

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
HELK_INFO_TAG = "[HELK_INFO]"

def run_command(command):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=False, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"{HELK_INFO_TAG} Error running command: {e.cmd}. Output: {e.output.strip()}")
        return None

def update_repo(local_repo_path):
    """Pull the repository or notify if it needs pushing or has diverged."""
    if os.path.exists(local_repo_path):
        logging.info(f"{HELK_INFO_TAG} Fetching updates for SIGMA remote...")
        run_command(["git", "-C", local_repo_path, "fetch"])

        logging.info(f"{HELK_INFO_TAG} Checking to see if local SIGMA repo is up to date or not...")
        local = run_command(["git", "-C", local_repo_path, "rev-parse", "@"])
        remote = run_command(["git", "-C", local_repo_path, "rev-parse", "@{u}"])
        base = run_command(["git", "-C", local_repo_path, "merge-base", "@", "@{u}"])

        if local == remote:
            logging.info(f"{HELK_INFO_TAG} [++++++] Local SIGMA repo is up-to-date...")
        elif local == base:
            logging.info(f"{HELK_INFO_TAG} [++++++] Local SIGMA repo needs to be updated. Updating local SIGMA repo...")
            run_command(["git", "-C", local_repo_path, "pull"])
        elif remote == base:
            logging.info(f"{HELK_INFO_TAG} [++++++] Need to push")
        else:
            logging.info(f"{HELK_INFO_TAG} [++++++] Diverged")
    else:
        logging.info(f"{HELK_INFO_TAG} Cloning the repository.")
        run_command(["git", "clone", SIGMA_REPO_URL, local_repo_path])
        
def list_updated_files(local_repo_path):
    """List the files that have been updated or created in the repository."""
    logging.info(f"{HELK_INFO_TAG} Listing updated or created files...")
    result = run_command(["git", "-C", local_repo_path, "log", "--name-status", "-1"])
    if result:
        logging.info(result)

def convert_sigma_to_elastalert():
    """Convert Sigma rules to ElastAlert format."""
    os.makedirs(ELASTALERT_RULES_DIR, exist_ok=True)
    sigma_rules_path = os.path.join(SIGMA_REPO_DIR, 'rules')
    
    for root, _, files in os.walk(sigma_rules_path):
        for file in files:
            if file.endswith('.yml'):
                sigma_rule_path = os.path.join(root, file)
                rule_name = os.path.splitext(file)[0]  # Get rule name without extension       
                # Create directory structure in elastalert_rules similar to Sigma rules
                relative_path = os.path.relpath(root, start=sigma_rules_path)
                elastalert_rule_dir = os.path.join(ELASTALERT_RULES_DIR, relative_path)
                os.makedirs(elastalert_rule_dir, exist_ok=True)
                
                elastalert_rule_path = os.path.join(elastalert_rule_dir, file)
                
                # Convert Sigma rule to ElastAlert format
                subprocess.run(['/home/rafiq/sigma/tools/sigmac', '-t', 'elastalert', '-c', 'sigmac_config.yml', sigma_rule_path, '-o', elastalert_rule_path])


def modify_elastalert_rules():
    """Modify ElastAlert rules by applying necessary changes and maintaining the original folder structure."""
    yaml = YAML()
    
    for root, _, files in os.walk(ELASTALERT_RULES_DIR):
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

# def modify_elastalert_rules():
#     """Modify ElastAlert rules by applying necessary changes and maintaining the original folder structure."""
#     yaml = ruamel.yaml.YAML()
#     os.makedirs(MODIFIED_RULES_DIR, exist_ok=True)
    
#     for root, _, files in os.walk(ELASTALERT_RULES_DIR):
#         for file in files:
#             if file.endswith('.yml') or file.endswith('.yaml'):
#                 elastalert_rule = os.path.join(root, file)
                
#                 # Read the content of the ElastAlert rule
#                 with open(elastalert_rule, 'r') as f:
#                     content = f.read()
                
#                 # If the file is empty, delete it
#                 if not content.strip():
#                     os.remove(elastalert_rule)
#                     logging.info(f"Deleted empty rule file: {elastalert_rule}")
#                     continue
                
#                 # Load the content as YAML
#                 try:
#                     data = yaml.load(content)
#                 except Exception as e:
#                     logging.error(f"Error loading YAML content from {elastalert_rule}: {e}")
#                     continue
                
#                 # Update the "name" field
#                 rule_name = os.path.splitext(file)[0]
#                 data['name'] = rule_name
#                 data['is_enabled'] = False
                
#                 # Determine the relative path of the file from the ELASTALERT_RULES_DIR
#                 relative_path = os.path.relpath(elastalert_rule, ELASTALERT_RULES_DIR)
#                 modified_rule_dir = os.path.dirname(os.path.join(MODIFIED_RULES_DIR, relative_path))
                
#                 # Ensure the directory exists
#                 os.makedirs(modified_rule_dir, exist_ok=True)
                
#                 # Save the modified rule with a .yaml extension
#                 modified_rule_path = os.path.join(modified_rule_dir, f"{rule_name}.yaml")
#                 try:
#                     with open(modified_rule_path, 'w') as f:
#                         yaml.dump(data, f)
#                     logging.info(f"Saved modified rule to {modified_rule_path}")
#                 except Exception as e:
#                     logging.error(f"Error saving modified rule to {modified_rule_path}: {e}")
                
#                 # Remove the original file if it exists in the modified directory
#                 original_file_path = os.path.join(modified_rule_dir, file)
#                 if os.path.exists(original_file_path):
#                     os.remove(original_file_path)
#                     logging.info(f"Removed original rule file: {original_file_path}")

def main():
    """Main function to orchestrate the update process."""
    try:
        while True:
            try:
                update_repo(SIGMA_REPO_DIR)
                list_updated_files(SIGMA_REPO_DIR)
                if ENABLE_ELASTALERT_CONVERSION:
                    convert_sigma_to_elastalert()
                modify_elastalert_rules()
                logging.info("SIEM rules update completed successfully.")
            except Exception as e:
                logging.error(f"An error occurred during the SIEM rules update process: {e}")
  
            logging.info(f"{HELK_INFO_TAG} Waiting for next update in {UPDATE_INTERVAL_HOURS} hours...")
            time.sleep(UPDATE_INTERVAL_HOURS * 3600)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected. Exiting.")

if __name__ == "__main__":
    main()