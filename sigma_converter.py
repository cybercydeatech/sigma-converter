import os
import subprocess
import logging
import git
import yaml
from datetime import datetime
import shutil
import time

# Configuration
REPO_URL = "https://github.com/Rafiq-uz-zaman/sigma_rule_01"
LOCAL_REPO_PATH = "./sigma_rule_01"
# SIGMA_RULE_PATH = ""
ELASTALERT_RULES_PATH = "../sigma_rules/sigma/rules"
helk_sigmac = f"${REPO_URL}/sigmac-config.yml"
# ENABLE_ELASTALERT_CONVERSION = True  # Set this to False to disable ElastAlert conversion
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
    """
    Pull the repository or notify if it needs pushing or has diverged.
    """
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
        run_command(["git", "clone", "https://github.com/Rafiq-uz-zaman/sigma_rule_01.git", local_repo_path])
        
def list_updated_files(local_repo_path):
    """
    List the files that have been updated or created in the repository.
    """
    logging.info(f"{HELK_INFO_TAG} Listing updated or created files...")
    result = run_command(["git", "-C", local_repo_path, "log", "--name-status", "-1"])
    if result:
        logging.info(result)

# def convert_sigma_rules():
#     rule_counter = 0
#     for rule_category in os.listdir(f"${REPO_URL}/rules/windows"):
#         rule_category_path = f"${REPO_URL}/rules/windows/{rule_category}"
#         if not os.path.isdir(rule_category_path):
#             continue

#         print(f"\n{HELK_INFO_TAG} Working on Folder: {rule_category_path}:")
#         print("-------------------------------------------------------------")

#         for rule in os.listdir(rule_category_path):
#             rule_path = os.path.join(rule_category_path, rule)
#             print(f"[+++] Processing Windows rule: {rule_path} ..")
#             # Run sigmac command to convert the rule for Sysmon
#             sigmac_command = f"tools/sigmac -t elastalert -c tools/config/generic/sysmon.yml -c {helk_sigmac} --backend-option timestamp_field=etl_processed_time -o {REPO_URL}/rules/sigma_sysmon_{rule} {rule_path}"
#             run_command(sigmac_command)

#             # Give a unique rule name for Sysmon
#             sysmon_rule_path = f"{REPO_URL}/rules/sigma_sysmon_{rule}"
#             with open(sysmon_rule_path, 'r') as file:
#                 sysmon_rule_content = file.read()
#             sysmon_rule_content = sysmon_rule_content.replace("name: ", "name: Sysmon_")
#             with open(sysmon_rule_path, 'w') as file:
#                 file.write(sysmon_rule_content)

#             # Run sigmac command for Windows Audit
#             sigmac_command = f"tools/sigmac -t elastalert -c tools/config/generic/windows-audit.yml -c {helk_sigmac} --backend-option timestamp_field=etl_processed_time -o {REPO_URL}/rules/sigma_{rule} {rule_path}"
#             run_command(sigmac_command)

#             rule_counter += 1

def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
    """
    Convert Sigma rules to ElastAlert format.
    """
    logging.info(f"{HELK_INFO_TAG} Converting Sigma rules to ElastAlert format...")

    # Ensure the ElastAlert rules directory exists
    if not os.path.exists(elastalert_rules_path):
        os.makedirs(elastalert_rules_path)

    try:
        # Iterate over Sigma rules files
        for root, _, files in os.walk(sigma_rules_path):
            for file in files:
                if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
                    sigma_rule_path = os.path.join(root, file)
                    with open(sigma_rule_path, "r") as sigma_file:
                        try:
                            sigma_rule = yaml.safe_load(sigma_file)
                        except yaml.YAMLError as exc:
                            logging.warning(f"{HELK_INFO_TAG} Error loading YAML in file {sigma_rule_path}: {exc}")
                            continue  # Skip invalid YAML file

                    if isinstance(sigma_rule, dict) and "title" in sigma_rule:
                        # Transform Sigma rule to ElastAlert rule
                        elastalert_rule = {
                            "rule": {
                                "name": sigma_rule["title"],
                                "description": sigma_rule.get("description", ""),
                                # Add more fields as needed based on ElastAlert rule configuration
                            },
                            # Add more sections (e.g., filter, alert, etc.) based on ElastAlert rule structure
                        }

                        # Write ElastAlert rule to file
                        elastalert_rule_file = os.path.join(elastalert_rules_path, f"{sigma_rule['title']}.yaml")
                        with open(elastalert_rule_file, "w") as elastalert_file:
                            yaml.dump(elastalert_rule, elastalert_file)
                    else:
                        logging.warning(f"{HELK_INFO_TAG} Skipping invalid Sigma rule in file: {sigma_rule_path}")

        logging.info(f"{HELK_INFO_TAG} Conversion completed successfully.")
    except Exception as e:
        logging.error(f"{HELK_INFO_TAG} Error converting Sigma rules to ElastAlert format: {e}")

def main():
    """
    Main function to orchestrate the update process.
    """
    try:
        while True:
            try:
                update_repo(LOCAL_REPO_PATH)
                list_updated_files(LOCAL_REPO_PATH)
                convert_to_elastalert_format(LOCAL_REPO_PATH, ELASTALERT_RULES_PATH)
            # update_siem_rules(LOCAL_REPO_PATH, ELASTALERT_RULES_PATH)
                logging.info("SIEM rules update completed successfully.")
            except Exception as e:
                logging.error(f"An error occurred during the SIEM rules update process: {e}")
  
            logging.info(f"{HELK_INFO_TAG} Waiting for next update in {UPDATE_INTERVAL_HOURS} hours...")
            time.sleep(UPDATE_INTERVAL_HOURS * 3600)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt dectected. Existing")

if __name__ == "__main__":
    main()

# def main():
#     """
#     Main function to orchestrate the update process.
#     """
#     while True:
#         try:
#             update_repo(LOCAL_REPO_PATH)
#             updated_files = list_updated_files(LOCAL_REPO_PATH)
#             # update_siem_rules(LOCAL_REPO_PATH, ELASTALERT_RULES_PATH, updated_files)
#             logging.info("SIEM rules update completed successfully.")
#         except Exception as e:
#             logging.error(f"An error occurred during the SIEM rules update process: {e}")
        
#         # Wait for the next update interval
#         logging.info(f"{HELK_INFO_TAG} Waiting for next update in {UPDATE_INTERVAL_HOURS} hours...")
#         time.sleep(UPDATE_INTERVAL_HOURS * 3600)

# if __name__ == "__main__":
#     main()