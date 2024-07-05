import os
import subprocess
import logging
import shutil
import time
from datetime import datetime
import ruamel.yaml
from ruamel.yaml import YAML

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
HELK_INFO_TAG = "[HELK_INFO]"

def load_config():
    """Load configuration from a YAML file."""
    yaml = ruamel.yaml.YAML(typ='safe', pure=True)
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    return config

def run_command(command):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"{HELK_INFO_TAG} Error running command: {e.cmd}. Output: {e.output.strip()}")
        return None

def update_repo(local_repo_path):
    """Pull the repository or notify if it needs pushing or has diverged."""
    if os.path.exists(local_repo_path):
        logging.info(f"{HELK_INFO_TAG} Fetching updates for SIGMA remote...")
        run_command(["git", "-C", local_repo_path, "fetch"])

        logging.info(f"{HELK_INFO_TAG} Checking if local SIGMA repo is up to date...")
        local = run_command(["git", "-C", local_repo_path, "rev-parse", "@"])
        remote = run_command(["git", "-C", local_repo_path, "rev-parse", "@{u}"])
        base = run_command(["git", "-C", local_repo_path, "merge-base", "@", "@{u}"])

        if local == remote:
            logging.info(f"{HELK_INFO_TAG} Local SIGMA repo is up-to-date.")
        elif local == base:
            logging.info(f"{HELK_INFO_TAG} Local SIGMA repo needs update. Updating...")
            run_command(["git", "-C", local_repo_path, "pull"])
        elif remote == base:
            logging.info(f"{HELK_INFO_TAG} Need to push")
        else:
            logging.info(f"{HELK_INFO_TAG} Diverged")
    else:
        logging.info(f"{HELK_INFO_TAG} Cloning the repository.")
        run_command(["git", "clone", load_config()['SIGMA_REPO_URL'], local_repo_path])

def list_updated_files(local_repo_path):
    """List the files that have been updated or created in the repository."""
    logging.info(f"{HELK_INFO_TAG} Listing updated or created files...")
    result = run_command(["git", "-C", local_repo_path, "log", "--name-status", "-1"])
    if result:
        logging.info(result)

def convert_sigma_to_elastalert(sigma_rules_path, elastalert_rules_dir):
    """Convert Sigma rules to ElastAlert format."""
    os.makedirs(elastalert_rules_dir, exist_ok=True)
    
    for root, _, files in os.walk(sigma_rules_path):
        for file in files:
            if file.endswith('.yml'):
                sigma_rule_path = os.path.join(root, file)
                rule_name = os.path.splitext(file)[0]
                relative_path = os.path.relpath(root, start=sigma_rules_path)
                elastalert_rule_dir = os.path.join(elastalert_rules_dir, relative_path)
                os.makedirs(elastalert_rule_dir, exist_ok=True)
                elastalert_rule_path = os.path.join(elastalert_rule_dir, file)
                subprocess.run(['/home/rafiq/sigma/tools/sigmac', '-t', 'elastalert', '-c', 'sigmac_config.yml', sigma_rule_path, '-o', elastalert_rule_path])

def modify_elastalert_rules(elastalert_rules_dir, modified_rules_dir):
    """Modify ElastAlert rules by applying necessary changes and maintaining the original folder structure."""
    yaml = YAML()
    
    for root, _, files in os.walk(elastalert_rules_dir):
        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                elastalert_rule = os.path.join(root, file)
                
                logging.info(f"Processing rule file: {elastalert_rule}")
                
                with open(elastalert_rule, 'r') as f:
                    content = f.read()
                
                if not content.strip():
                    os.remove(elastalert_rule)
                    logging.info(f"Deleted empty rule file: {elastalert_rule}")
                    continue
                
                try:
                    data = yaml.load(content)
                except Exception as e:
                    logging.error(f"Error loading YAML content from {elastalert_rule}: {e}")
                    continue
                
                rule_name = os.path.splitext(file)[0]
                data['name'] = rule_name
                
                if 'is_enabled' not in data:
                    data['is_enabled'] = False
                data['timestamp_type'] = '@timestamp'
                modified_rule_path = os.path.join(root, f"{rule_name}.yaml")
                try:
                    with open(modified_rule_path, 'w') as f:
                        yaml.dump(data, f)
                    logging.info(f"Saved modified rule to {modified_rule_path}")
                except Exception as e:
                    logging.error(f"Error saving modified rule to {modified_rule_path}: {e}")
                
                if elastalert_rule != modified_rule_path and os.path.exists(elastalert_rule):
                    os.remove(elastalert_rule)
                    logging.info(f"Removed original rule file: {elastalert_rule}")

def main():
    """Main function to orchestrate the update process."""
    config = load_config()
    try:
        while True:
            try:
                # update_repo(config['SIGMA_REPO_DIR'])
                # list_updated_files(config['SIGMA_REPO_DIR'])
                
                if config['ENABLE_ELASTALERT_CONVERSION']:
                    # convert_sigma_to_elastalert(os.path.join(config['SIGMA_REPO_DIR'], 'rules'), config['ELASTALERT_RULES_DIR'])
                
                    modify_elastalert_rules(config['ELASTALERT_RULES_DIR'], config['MODIFIED_RULES_DIR'])
                
                logging.info("SIEM rules update completed successfully.")
            except Exception as e:
                logging.error(f"An error occurred during the SIEM rules update process: {e}")
  
            logging.info(f"{HELK_INFO_TAG} Waiting for next update in {config['UPDATE_INTERVAL_HOURS']} hours...")
            time.sleep(config['UPDATE_INTERVAL_HOURS'] * 3600)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected. Exiting.")

if __name__ == "__main__":
    main()
