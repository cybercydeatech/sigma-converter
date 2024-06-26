import os
import subprocess
import logging
import git
import yaml
from datetime import datetime, timedelta
import shutil
import time
from git import Repo

# Configuration


REPO_URL = "https://github.com/SigmaHQ/sigma.git"
LOCAL_REPO_PATH = "./sigma/rules"
ELASTALERT_RULES_PATH = "./sigma_rules_01/converted_sigma_rules"
# helk_sigmac = f"${REPO_URL}/sigmac-config.yml"
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
        run_command(["git", "clone", "https://github.com/SigmaHQ/sigma.git", local_repo_path])
        
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
#     for rule_category in os.listdir(f"${REPO_URL}/rules"):
#         rule_category_path = f"${REPO_URL}/rules/{rule_category}"
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


# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """
#     Convert Sigma rules to ElastAlert format.
#     """
#     logging.info(f"{HELK_INFO_TAG} Converting Sigma rules to ElastAlert format...")

#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     with open(sigma_rule_path, "r") as sigma_file:
#                         try:
#                             sigma_rule = yaml.safe_load(sigma_file)
#                         except yaml.YAMLError as exc:
#                             logging.warning(f"{HELK_INFO_TAG} Error loading YAML in file {sigma_rule_path}: {exc}")
#                             continue  # Skip invalid YAML file

#                     if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                         # Transform Sigma rule to ElastAlert rule
#                         elastalert_rule = {
#                             "rule": {
#                                 "name": sigma_rule["title"],
#                                 "description": sigma_rule.get("description", ""),
#                                 # Add more fields as needed based on ElastAlert rule configuration
#                             },
#                             # Add more sections (e.g., filter, alert, etc.) based on ElastAlert rule structure
#                         }

#                         # Write ElastAlert rule to file
#                         elastalert_rule_file = os.path.join(elastalert_rules_path, f"{sigma_rule['title']}.yaml")
#                         with open(elastalert_rule_file, "w") as elastalert_file:
#                             yaml.dump(elastalert_rule, elastalert_file)
#                     else:
#                         logging.warning(f"{HELK_INFO_TAG} Skipping invalid Sigma rule in file: {sigma_rule_path}")

#         logging.info(f"{HELK_INFO_TAG} Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"{HELK_INFO_TAG} Error converting Sigma rules to ElastAlert format: {e}")




# def fetch_sigma_rules(sigma_repo_url, local_sigma_rules_path):
#     """
#     Fetch Sigma rules from a remote repository.
#     """
#     logging.info(f"{HELK_INFO_TAG} Fetching Sigma rules from {sigma_repo_url}...")

#     try:
#         # Clone the repository if it doesn't exist locally
#         if not os.path.exists(local_sigma_rules_path):
#             Repo.clone_from(sigma_repo_url, local_sigma_rules_path)
#         else:
#             # Pull latest changes if the repository exists locally
#             repo = Repo(local_sigma_rules_path)
#             origin = repo.remotes.origin
#             origin.pull()

#         logging.info(f"{HELK_INFO_TAG} Sigma rules fetched successfully.")
#     except Exception as e:
#         logging.error(f"{HELK_INFO_TAG} Error fetching Sigma rules: {e}")



# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """
#     Convert newly added or modified Sigma rules to ElastAlert format.
#     """
#     logging.info(f"{HELK_INFO_TAG} Converting newly added or modified Sigma rules to ElastAlert format...")

#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Track last conversion time
#         last_conversion_time_file = os.path.join(elastalert_rules_path, "last_conversion_time.txt")
#         if os.path.exists(last_conversion_time_file):
#             with open(last_conversion_time_file, "r") as f:
#                 last_conversion_time = datetime.fromisoformat(f.read())
#         else:
#             last_conversion_time = datetime.min

#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)

#                     # Check last modification time
#                     last_modified_time = datetime.fromtimestamp(os.path.getmtime(sigma_rule_path))
#                     if last_modified_time <= last_conversion_time:
#                         continue  # Skip if file hasn't been modified since last conversion

#                     with open(sigma_rule_path, "r") as sigma_file:
#                         try:
#                             sigma_rule = yaml.safe_load(sigma_file)
#                         except yaml.YAMLError as exc:
#                             logging.warning(f"{HELK_INFO_TAG} Error loading YAML in file {sigma_rule_path}: {exc}")
#                             continue  # Skip invalid YAML file

#                     if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                         # Transform Sigma rule to ElastAlert rule
#                         elastalert_rule = {
#                             "rule": {
#                                 "name": sigma_rule["title"],
#                                 "description": sigma_rule.get("description", ""),
#                                 # Add more fields as needed based on ElastAlert rule configuration
#                             },
#                             # Add more sections (e.g., filter, alert, etc.) based on ElastAlert rule structure
#                         }

#                         # Write ElastAlert rule to file
#                         elastalert_rule_file = os.path.join(elastalert_rules_path, f"{sigma_rule['title']}.yaml")
#                         with open(elastalert_rule_file, "w") as elastalert_file:
#                             yaml.dump(elastalert_rule, elastalert_file)
#                     else:
#                         logging.warning(f"{HELK_INFO_TAG} Skipping invalid Sigma rule in file: {sigma_rule_path}")

#         # Update last conversion time
#         with open(last_conversion_time_file, "w") as f:
#             f.write(datetime.now().isoformat())

#         logging.info(f"{HELK_INFO_TAG} Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"{HELK_INFO_TAG} Error converting Sigma rules to ElastAlert format: {e}")



# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format."""
#     logging.info("Converting Sigma rules to ElastAlert format...")
#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Logic for conversion
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)

#                     # Check last modification time
#                     last_modified_time = datetime.fromtimestamp(os.path.getmtime(sigma_rule_path))
                    
#                     with open(sigma_rule_path, "r") as sigma_file:
#                         try:
#                             sigma_rule = yaml.safe_load(sigma_file)
#                         except yaml.YAMLError as exc:
#                             logging.warning(f"Error loading YAML in file {sigma_rule_path}: {exc}")
#                             continue  # Skip invalid YAML file

#                     if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                         # Transform Sigma rule to ElastAlert rule
#                         elastalert_rule = {
#                             "rule": {
#                                 "name": sigma_rule["title"],
#                                 "description": sigma_rule.get("description", ""),
#                                 # Add more fields as needed based on ElastAlert rule configuration
#                             },
#                             # Add more sections (e.g., filter, alert, etc.) based on ElastAlert rule structure
#                         }

#                         # Write ElastAlert rule to file
#                         elastalert_rule_file = os.path.join(elastalert_rules_path, f"{sigma_rule['title']}.yaml")
#                         # Ensure directories leading to the file exist
#                         os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                         with open(elastalert_rule_file, "w") as elastalert_file:
#                             yaml.dump(elastalert_rule, elastalert_file)
#                     else:
#                         logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")

#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")



# main
# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format."""
#     logging.info("Converting Sigma rules to ElastAlert format...")
#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     # subprocess.run(['/home/rafiq/sigma/tools/sigmac', '-t', 'elastalert', '-c', 'sigmac_config.yml', sigma_rule_path, '-o', sigma_rule])
#                     logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

#                     # Check if the file is updated or added
#                     last_modified_time = datetime.fromtimestamp(os.path.getmtime(sigma_rule_path))
#                     last_conversion_time = datetime.now() - timedelta(hours=UPDATE_INTERVAL_HOURS)
#                     logging.info(f"Last modified time: {last_modified_time}")
#                     logging.info(f"Last conversion time: {last_conversion_time}")

#                     if last_modified_time > last_conversion_time:
#                         # Convert only if the file is updated or added after the last conversion time
#                         elastalert_rule_file = os.path.join(elastalert_rules_path, os.path.relpath(sigma_rule_path, sigma_rules_path))
#                         os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                         subprocess.run(['/home/rafiq/sigma/tools/sigmac', '-t', 'elastalert', '-c', 'sigmac_config.yml', sigma_rule_path, '-o', sigma_rule])
#                         logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

#                         with open(sigma_rule_path, "r") as sigma_file:
#                             sigma_rule = yaml.safe_load(sigma_file)

#                         if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                             # Write ElastAlert rule to file
#                             with open(elastalert_rule_file, "w") as elastalert_file:
#                                 yaml.dump(sigma_rule, elastalert_file)
#                         else:
#                             logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")
#                     else:
#                         logging.info(f"Skipping Sigma rule file: {sigma_rule_path}, not updated or added recently")
        
#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")




# def convert_sigma_to_elastalert():
#     os.makedirs(ELASTALERT_RULES_PATH, exist_ok=True)
#     sigma_rules_path = os.path.join(LOCAL_REPO_PATH, 'rules')
#     for root, _, files in os.walk(sigma_rules_path):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule = os.path.join(root, file)
#                 elastalert_rule = os.path.join(ELASTALERT_RULES_PATH, file)
#                 subprocess.run(['/home/rafiq/sigma/tools/sigmac', '-t', 'elastalert', '-c', 'sigmac_config.yml', sigma_rule, '-o', elastalert_rule])

# def convert_sigma_to_elastalert():
#     os.makedirs(ELASTALERT_RULES_PATH, exist_ok=True)
#     sigma_rules_path = os.path.join(LOCAL_REPO_PATH, 'rules')
    
#     for root, _, files in os.walk(sigma_rules_path):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule_path = os.path.join(root, file)
#                 rule_name = os.path.splitext(file)[0]  # Get rule name without extension
                
#                 # Create directory structure in elastalert_rules similar to Sigma rules
#                 relative_path = os.path.relpath(root, start=sigma_rules_path)
#                 elastalert_rule_dir = os.path.join(ELASTALERT_RULES_PATH, relative_path)
#                 os.makedirs(elastalert_rule_dir, exist_ok=True)
                
#                 elastalert_rule_path = os.path.join(elastalert_rule_dir, file)
                
#                 # Convert Sigma rule to ElastAlert format
#                 subprocess.run(['/home/rafiq/sigma/tools/sigmac', '-t', 'elastalert', '-c', 'sigmac_config.yml', sigma_rule_path, '-o', elastalert_rule_path])





# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format."""
#     logging.info("Converting Sigma rules to ElastAlert format...")
#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

#                     # Check if the file is updated or added
#                     last_modified_time = datetime.fromtimestamp(os.path.getmtime(sigma_rule_path))
#                     last_conversion_time = datetime.now() - timedelta(hours=UPDATE_INTERVAL_HOURS)
#                     logging.info(f"Last modified time: {last_modified_time}")
#                     logging.info(f"Last conversion time: {last_conversion_time}")

#                     if last_modified_time > last_conversion_time:
#                         # Convert only if the file is updated or added after the last conversion time
#                         elastalert_rule_file = os.path.join(elastalert_rules_path, os.path.relpath(sigma_rule_path, sigma_rules_path))
#                         os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                         logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

#                         # Load the Sigma rule from the YAML file
#                         with open(sigma_rule_path, "r") as sigma_file:
#                             sigma_rule = yaml.safe_load(sigma_file)

#                         if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                             # Write ElastAlert rule to file
#                             with open(elastalert_rule_file, "w") as elastalert_file:
#                                 yaml.dump(sigma_rule, elastalert_file)
#                         else:
#                             logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")
#                     else:
#                         logging.info(f"Skipping Sigma rule file: {sigma_rule_path}, not updated or added recently")
        
#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")



# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format."""
#     logging.info("Converting Sigma rules to ElastAlert format...")

#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)
#         logging.info(f"Created ElastAlert rules directory: {elastalert_rules_path}")

#     try:
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

#                     try:
#                         # Check if the file is updated or added
#                         last_modified_time = datetime.fromtimestamp(os.path.getmtime(sigma_rule_path))
#                         last_conversion_time = datetime.now() - timedelta(hours=UPDATE_INTERVAL_HOURS)
#                         logging.debug(f"File last modified time: {last_modified_time}")
#                         logging.debug(f"Last conversion time: {last_conversion_time}")

#                         if last_modified_time > last_conversion_time:
#                             # Convert only if the file is updated or added after the last conversion time
#                             elastalert_rule_file = os.path.join(elastalert_rules_path, os.path.relpath(sigma_rule_path, sigma_rules_path))
#                             os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                             logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

#                             # Load the Sigma rule from the YAML file
#                             with open(sigma_rule_path, "r") as sigma_file:
#                                 sigma_rule = yaml.safe_load(sigma_file)

#                             # Add debugging info to validate loaded YAML content
#                             logging.debug(f"Loaded Sigma rule content: {sigma_rule}")

#                             if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                                 # Write ElastAlert rule to file
#                                 with open(elastalert_rule_file, "w") as elastalert_file:
#                                     yaml.dump(sigma_rule, elastalert_file)
#                                 logging.info(f"Successfully converted and saved ElastAlert rule: {elastalert_rule_file}")
#                             else:
#                                 logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")
#                         else:
#                             logging.info(f"Skipping Sigma rule file: {sigma_rule_path}, not updated or added recently")
#                     except Exception as e:
#                         logging.error(f"Error processing Sigma rule file {sigma_rule_path}: {e}")

#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")





# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format."""
#     logging.info("Converting Sigma rules to ElastAlert format...")
#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

#                     # Check if the file is updated or added
#                     last_modified_time = datetime.fromtimestamp(os.path.getmtime(sigma_rule_path))
#                     last_conversion_time = datetime.now() - timedelta(hours=UPDATE_INTERVAL_HOURS)
#                     logging.info(f"Last modified time: {last_modified_time}")
#                     logging.info(f"Last conversion time: {last_conversion_time}")

#                     if last_modified_time > last_conversion_time:
#                         # Convert only if the file is updated or added after the last conversion time
#                         elastalert_rule_file = os.path.join(elastalert_rules_path, os.path.relpath(sigma_rule_path, sigma_rules_path))
#                         elastalert_rule_file = os.path.splitext(elastalert_rule_file)[0] + ".yaml"  # Change extension to .yaml
#                         os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                         logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

#                         with open(sigma_rule_path, "r") as sigma_file:
#                             sigma_rule = yaml.safe_load(sigma_file)

#                         if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                             # Transform Sigma rule to ElastAlert rule
#                             # elastalert_rule = {
#                             #     "rule": {
#                             #         "name": sigma_rule["title"],
#                             #         "description": sigma_rule.get("description", ""),
#                             #         # Add more fields as needed based on ElastAlert rule configuration
#                             #     },
#                             #     # Add more sections (e.g., filter, alert, etc.) based on ElastAlert rule structure
#                             # }

#                             # Write ElastAlert rule to file
#                             with open(elastalert_rule_file, "w") as elastalert_file:
#                                 yaml.dump(sigma_rule, elastalert_file)
#                         else:
#                             logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")
#                     else:
#                         logging.info(f"Skipping Sigma rule file: {sigma_rule_path}, not updated or added recently")
        
#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")

# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format."""
#     logging.info("Converting Sigma rules to ElastAlert format...")
#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Load or create a file to store last modified times of rules
#         last_modified_file = os.path.join(elastalert_rules_path, "last_modified_times.txt")
#         if os.path.exists(last_modified_file):
#             with open(last_modified_file, "r") as f:
#                 last_modified_times = yaml.safe_load(f)
#         else:
#             last_modified_times = {}

#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

#                     # Check if the file is updated or added
#                     last_modified_time = datetime.fromtimestamp(os.path.getmtime(sigma_rule_path))
#                     last_conversion_time = last_modified_times.get(sigma_rule_path, datetime.min)

#                     if last_modified_time > last_conversion_time:
#                         # Convert only if the rule is updated or added after the last conversion time
#                         elastalert_rule_file = os.path.join(elastalert_rules_path, os.path.relpath(sigma_rule_path, sigma_rules_path))
#                         os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                         logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

#                         with open(sigma_rule_path, "r") as sigma_file:
#                             sigma_rule = yaml.safe_load(sigma_file)

#                         if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                             # Transform Sigma rule to ElastAlert rule
#                             # elastalert_rule = {
#                             #     "rule": {
#                             #         "name": sigma_rule["title"],
#                             #         "description": sigma_rule.get("description", ""),
                                    
#                             #         # Add more fields as needed based on ElastAlert rule configuration
#                             #     },
#                             #     # Add more sections (e.g., filter, alert, etc.) based on ElastAlert rule structure
#                             # }

#                             # Write ElastAlert rule to file
#                             with open(elastalert_rule_file, "w") as elastalert_file:
#                                 yaml.dump(sigma_rule, elastalert_file)
#                         else:
#                             logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")

#                         # Update last modified time for the rule
#                         last_modified_times[sigma_rule_path] = last_modified_time

#         # Save the last modified times back to the file
#         with open(last_modified_file, "w") as f:
#             yaml.dump(last_modified_times, f)

#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")


def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
    """Convert Sigma rules to ElastAlert format."""
    logging.info("Converting Sigma rules to ElastAlert format...")
    
    # Ensure the ElastAlert rules directory exists
    if not os.path.exists(elastalert_rules_path):
        os.makedirs(elastalert_rules_path)

    try:
        # Iterate over Sigma rules files
        for root, _, files in os.walk(sigma_rules_path):
            for file in files:
                if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
                    sigma_rule_path = os.path.join(root, file)
                    logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

                    # Convert Sigma rule to ElastAlert format
                    elastalert_rule_file = os.path.join(elastalert_rules_path, os.path.relpath(sigma_rule_path, sigma_rules_path))
                    os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
                    logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

                    with open(sigma_rule_path, "r") as sigma_file:
                        sigma_rule = yaml.safe_load(sigma_file)

                    if isinstance(sigma_rule, dict) and "title" in sigma_rule:
                        # Transform Sigma rule to ElastAlert rule
                        # Here you need to construct the ElastAlert rule based on your specific requirements.
                        # Example structure:
                        # elastalert_rule = {
                        #     "rule": {
                        #         "name": sigma_rule["title"],
                        #         "description": sigma_rule.get("description", ""),
                        #         # Add more fields as needed based on ElastAlert rule configuration
                        #     },
                        #     # Add more sections (e.g., filter, alert, etc.) based on ElastAlert rule structure
                        # }

                        # Write ElastAlert rule to file
                        with open(elastalert_rule_file, "w") as elastalert_file:
                            yaml.dump(sigma_rule, elastalert_file)
                    else:
                        logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")

        logging.info("Conversion completed successfully.")
    except Exception as e:
        logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")



# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format."""
#     logging.info("Converting Sigma rules to ElastAlert format...")
#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

#                     # Construct the ElastAlert rule file path with ".yaml" extension
#                     elastalert_rule_file = os.path.join(elastalert_rules_path, os.path.relpath(sigma_rule_path, sigma_rules_path))
#                     elastalert_rule_file = os.path.splitext(elastalert_rule_file)[0] + ".yaml"  # Change extension to .yaml
#                     os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                     logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

#                     with open(sigma_rule_path, "r") as sigma_file:
#                         sigma_rule = yaml.safe_load(sigma_file)

#                     if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                         # Transform Sigma rule to ElastAlert rule
#                         # elastalert_rule = {
#                         #     "rule": {
#                         #         "title": sigma_rule["title"],
#                         #         "id": sigma_rule.get("id", ""),
#                         #         "status": sigma_rule.get("status", ""),
#                         #         "description": sigma_rule.get("description", ""),
#                         #         "references": sigma_rule.get("references", []),
#                         #         "author": sigma_rule.get("author", ""),
#                         #         "date": sigma_rule.get("date", ""),
#                         #         "modified": sigma_rule.get("modified", ""),
#                         #         "tags": sigma_rule.get("tags", []),
#                         #         "logsource": sigma_rule.get("logsource", {}),
#                         #         "detection": sigma_rule.get("detection", {}),
#                         #         "falsepositives": sigma_rule.get("falsepositives", []),
#                         #         "level": sigma_rule.get("level", "")
#                         #         # Add more fields as needed based on ElastAlert rule configuration
#                         #     }
#                         # }

#                         # Write ElastAlert rule to file
#                         with open(elastalert_rule_file, "w") as elastalert_file:
#                             yaml.dump(sigma_rule, elastalert_file)
#                     else:
#                         logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")

#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")


# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format."""
#     logging.info("Converting Sigma rules to ElastAlert format...")
#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

#                     # Construct the ElastAlert rule file path with ".yaml" extension
#                     elastalert_rule_file = os.path.join(elastalert_rules_path, os.path.relpath(sigma_rule_path, sigma_rules_path))
#                     elastalert_rule_file = os.path.splitext(elastalert_rule_file)[0] + ".yaml"  # Change extension to .yaml
#                     os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                     logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

#                     with open(sigma_rule_path, "r") as sigma_file:
#                         sigma_rule = yaml.safe_load(sigma_file)

#                     if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                         # Write ElastAlert rule to file
#                         with open(elastalert_rule_file, "w") as elastalert_file:
#                             yaml.dump(sigma_rule, elastalert_file)
#                     else:
#                         logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")

#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")

# def modify_elastalert_rules():
#     os.makedirs(ELASTALERT_RULES_PATH, exist_ok=True)
#     for root, _, files in os.walk(ELASTALERT_RULES_PATH):
#         for file in files:
#             if file.endswith('.yaml'):
#                 elastalert_rule = os.path.join(root, file)
#                 modified_rule = os.path.join(ELASTALERT_RULES_PATH, file)
#                 with open(elastalert_rule, 'r') as f:
#                     content = f.read()
#                 # Apply necessary changes to the content
#                 modified_content = content.replace('old_value', 'new_value')
#                 with open(modified_rule, 'w') as f:
#                     f.write(modified_content)




# def convert_to_elastalert_format(sigma_rules_path, elastalert_rules_path):
#     """Convert Sigma rules to ElastAlert format and change the file extension to .yaml."""
#     logging.info("Converting Sigma rules to ElastAlert format...")

#     # Ensure the ElastAlert rules directory exists
#     if not os.path.exists(elastalert_rules_path):
#         os.makedirs(elastalert_rules_path)

#     try:
#         # Iterate over Sigma rules files
#         for root, _, files in os.walk(sigma_rules_path):
#             for file in files:
#                 if file.endswith(".yml"):  # Assuming Sigma rules are YAML files
#                     sigma_rule_path = os.path.join(root, file)
#                     logging.info(f"Processing Sigma rule file: {sigma_rule_path}")

#                     elastalert_rule_file = os.path.join(
#                         elastalert_rules_path, 
#                         os.path.relpath(sigma_rule_path, sigma_rules_path)
#                     ).replace('.yml', '.yaml')  # Change extension to .yaml
#                     os.makedirs(os.path.dirname(elastalert_rule_file), exist_ok=True)
#                     logging.info(f"Converting Sigma rule to ElastAlert format: {sigma_rule_path}")

#                     with open(sigma_rule_path, "r") as sigma_file:
#                         sigma_rule = yaml.safe_load(sigma_file)

#                     if isinstance(sigma_rule, dict) and "title" in sigma_rule:
#                         # Transform Sigma rule to ElastAlert rule
#                         # Assuming no actual transformation logic provided, just copying for now
#                         with open(elastalert_rule_file, "w") as elastalert_file:
#                             yaml.dump(sigma_rule, elastalert_file)
#                     else:
#                         logging.warning(f"Skipping invalid Sigma rule in file: {sigma_rule_path}")

#         logging.info("Conversion completed successfully.")
#     except Exception as e:
#         logging.error(f"Error converting Sigma rules to ElastAlert format: {e}")



# def convert_sigma_to_elastalert():
#     os.makedirs(ELASTALERT_RULES_DIR, exist_ok=True)
#     sigma_rules_path = os.path.join(SIGMA_REPO_DIR, 'rules')
#     for root, _, files in os.walk(sigma_rules_path):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule = os.path.join(root, file)
#                 elastalert_rule = os.path.join(ELASTALERT_RULES_DIR, file)
#                 subprocess.run(['/home/rafiq/sigma/tools/sigmac', '-t', 'elastalert', '-c', 'sigmac_config.yml', sigma_rule, '-o', elastalert_rule])


# def modify_elastalert_rules():
#     os.makedirs(MODIFIED_RULES_DIR, exist_ok=True)
#     for root, _, files in os.walk(ELASTALERT_RULES_DIR):
#         for file in files:
#             if file.endswith('.yml'):
#                 elastalert_rule = os.path.join(root, file)
#                 modified_rule = os.path.join(MODIFIED_RULES_DIR, file)
#                 with open(elastalert_rule, 'r') as f:
#                     content = f.read()
#                 # Apply necessary changes to the content
#                 modified_content = content.replace('old_value', 'new_value')
#                 with open(modified_rule, 'w') as f:
#                     f.write(modified_content)



# def convert_sigma_to_elastalert():
#     os.makedirs(ELASTALERT_RULES_DIR, exist_ok=True)
#     sigma_rules_path = os.path.join(SIGMA_REPO_DIR, 'rules')
    
#     for root, _, files in os.walk(sigma_rules_path):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule_path = os.path.join(root, file)
#                 rule_name = os.path.splitext(file)[0]  # Get rule name without extension
                
#                 # Load the Sigma rule
#                 with open(sigma_rule_path, 'r') as f:
#                     sigma_rule = yaml.safe_load(f)
                
#                 # Update the name in the Sigma rule
#                 sigma_rule['name'] = rule_name
                
#                 # Save the updated Sigma rule back to file
#                 with open(sigma_rule_path, 'w') as f:
#                     yaml.dump(sigma_rule, f, default_flow_style=False, allow_unicode=True)
                
#                 # Create directory structure in elastalert_rules similar to Sigma rules
#                 relative_path = os.path.relpath(root, start=sigma_rules_path)
#                 elastalert_rule_dir = os.path.join(ELASTALERT_RULES_DIR, relative_path)
#                 os.makedirs(elastalert_rule_dir, exist_ok=True)
                
#                 # Change the file extension to .yaml for ElastAlert
#                 elastalert_rule_filename = rule_name + '.yaml'
#                 elastalert_rule_path = os.path.join(elastalert_rule_dir, elastalert_rule_filename)
                
#                 # Convert Sigma rule to ElastAlert format
#                 subprocess.run([SIGMAC_TOOL_PATH, '-t', 'elastalert', '-c', SIGMAC_CONFIG_FILE, sigma_rule_path, '-o', elastalert_rule_path])

# NEW_SIGMA_RULES_DIR = 'new/sigma/rules'

# def create_new_sigma_rules_folder():
#     os.makedirs(NEW_SIGMA_RULES_DIR, exist_ok=True)
    
#     for root, _, files in os.walk(SIGMA_REPO_DIR):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule_path = os.path.join(root, file)
#                 rule_name = os.path.splitext(file)[0]  # Get rule name without extension
                
#                 # Load the Sigma rule
#                 with open(sigma_rule_path, 'r') as f:
#                     sigma_rule = yaml.safe_load(f)
                
#                 # Update the name field
#                 sigma_rule['name'] = rule_name
                
#                 # Save the updated Sigma rule to the new folder with .yaml extension
#                 new_rule_path = os.path.join(NEW_SIGMA_RULES_DIR, rule_name + '.yaml')
#                 with open(new_rule_path, 'w') as f:
#                     yaml.dump(sigma_rule, f, default_flow_style=False, allow_unicode=True)

# def convert_sigma_to_elastalert():
#     os.makedirs(ELASTALERT_RULES_DIR, exist_ok=True)
#     sigma_rules_path = os.path.join(SIGMA_REPO_DIR, 'rules')
    
#     for root, _, files in os.walk(sigma_rules_path):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule_path = os.path.join(root, file)
#                 rule_name = os.path.splitext(file)[0]
#                 # Create directory structure in elastalert_rules similar to Sigma rules
#                 relative_path = os.path.relpath(root, start=sigma_rules_path)
#                 elastalert_rule_dir = os.path.join(ELASTALERT_RULES_DIR, relative_path)
#                 os.makedirs(elastalert_rule_dir, exist_ok=True)
                
#                 elastalert_rule_path = os.path.join(elastalert_rule_dir, file)
                
#                 # Convert Sigma rule to ElastAlert format
#                 subprocess.run([SIGMAC_TOOL_PATH, '-t', 'elastalert', '-c', SIGMAC_CONFIG_FILE, sigma_rule_path, '-o', elastalert_rule_path])


# def convert_sigma_to_elastalert():
#     os.makedirs(ELASTALERT_RULES_DIR, exist_ok=True)
#     sigma_rules_path = os.path.join(SIGMA_REPO_DIR, 'rules')
    
#     for root, _, files in os.walk(sigma_rules_path):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule_path = os.path.join(root, file)
#                 rule_name = os.path.splitext(file)[0]
                
#                 # Load the Sigma rule
#                 with open(sigma_rule_path, 'r') as f:
#                     sigma_rule = yaml.safe_load(f)
                
#                 # Update the 'name' field in the Sigma rule
#                 sigma_rule['name'] = rule_name
                
#                 # Save the updated Sigma rule back to file
#                 with open(sigma_rule_path, 'w') as f:
#                     yaml.dump(sigma_rule, f, default_flow_style=False, allow_unicode=True)
                
#                 # Create directory structure in elastalert_rules similar to Sigma rules
#                 relative_path = os.path.relpath(root, start=sigma_rules_path)
#                 elastalert_rule_dir = os.path.join(ELASTALERT_RULES_DIR, relative_path)
#                 os.makedirs(elastalert_rule_dir, exist_ok=True)
                
#                 # Path to save ElastAlert rule file with the same name and .yaml extension
#                 elastalert_rule_path = os.path.join(elastalert_rule_dir, rule_name + '.yaml')
                
#                 # Convert Sigma rule to ElastAlert format
#                 subprocess.run([SIGMAC_TOOL_PATH, '-t', 'elastalert', '-c', SIGMAC_CONFIG_FILE, sigma_rule_path, '-o', elastalert_rule_path])



# def convert_sigma_to_elastalert():
#     os.makedirs(ELASTALERT_RULES_DIR, exist_ok=True)
#     sigma_rules_path = os.path.join(SIGMA_REPO_DIR, 'rules')
    
#     for root, _, files in os.walk(sigma_rules_path):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule_path = os.path.join(root, file)
#                 rule_name = os.path.splitext(file)[0]
                
#                 try:
#                     # Load the Sigma rule
#                     with open(sigma_rule_path, 'r', encoding='utf-8') as f:
#                         sigma_rule = yaml.safe_load(f)
                    
#                     # Debug: Print the loaded rule to verify its contents
#                     print(f"Loaded rule from {sigma_rule_path}: {sigma_rule}")

#                     # Update the 'name' field in the Sigma rule
#                     sigma_rule['name'] = rule_name
                    
#                     # Save the updated Sigma rule back to file
#                     with open(sigma_rule_path, 'w', encoding='utf-8') as f:
#                         yaml.dump(sigma_rule, f, default_flow_style=False, allow_unicode=True)
                    
#                     # Debug: Print confirmation of the updated rule
#                     print(f"Updated rule saved to {sigma_rule_path} with name: {rule_name}")

#                     # Create directory structure in elastalert_rules similar to Sigma rules
#                     relative_path = os.path.relpath(root, start=sigma_rules_path)
#                     elastalert_rule_dir = os.path.join(ELASTALERT_RULES_DIR, relative_path)
#                     os.makedirs(elastalert_rule_dir, exist_ok=True)
                    
#                     # Path to save ElastAlert rule file with the same name and .yaml extension
#                     elastalert_rule_path = os.path.join(elastalert_rule_dir, rule_name + '.yaml')
                    
#                     # Convert Sigma rule to ElastAlert format
#                     subprocess.run([SIGMAC_TOOL_PATH, '-t', 'elastalert', '-c', SIGMAC_CONFIG_FILE, sigma_rule_path, '-o', elastalert_rule_path], check=True)
                    
#                     # Debug: Print confirmation of the conversion
#                     return elastalert_rule_path

#                 except Exception as e:
#                     # Print the error for debugging purposes
#                     print(f"Error processing {sigma_rule_path}: {e}")


# def convert_sigma_to_elastalert():
#     os.makedirs(ELASTALERT_RULES_DIR, exist_ok=True)
#     sigma_rules_path = os.path.join(SIGMA_REPO_DIR, 'rules')
    
#     for root, _, files in os.walk(sigma_rules_path):
#         for file in files:
#             if file.endswith('.yml'):
#                 sigma_rule_path = os.path.join(root, file)
#                 rule_name = os.path.splitext(file)[0]
                
#                 try:
#                     # Load the Sigma rule
#                     with open(sigma_rule_path, 'r', encoding='utf-8') as f:
#                         sigma_rule = yaml.safe_load(f)

#                     # Check if the rule is loaded correctly and is a dictionary
#                     if isinstance(sigma_rule, dict):
#                         # Update the 'name' field in the Sigma rule
#                         sigma_rule['name'] = rule_name
                        
#                         # Save the updated Sigma rule back to file
#                         with open(sigma_rule_path, 'w', encoding='utf-8') as f:
#                             yaml.dump(sigma_rule, f, default_flow_style=False, allow_unicode=True)

#                     # Create directory structure in elastalert_rules similar to Sigma rules
#                     relative_path = os.path.relpath(root, start=sigma_rules_path)
#                     elastalert_rule_dir = os.path.join(ELASTALERT_RULES_DIR, relative_path)
#                     os.makedirs(elastalert_rule_dir, exist_ok=True)
                    
#                     # Path to save ElastAlert rule file with the same name and .yaml extension
#                     elastalert_rule_path = os.path.join(elastalert_rule_dir, rule_name + '.yaml')
                    
#                     # Convert Sigma rule to ElastAlert format
#                     subprocess.run([SIGMAC_TOOL_PATH, '-t', 'elastalert', '-c', SIGMAC_CONFIG_FILE, sigma_rule_path, '-o', elastalert_rule_path], check=True)

#                 except Exception as e:
#                     # Log the error if needed
#                     print(f"Error processing {sigma_rule_path}: {e}")

def main():
    """
    Main function to orchestrate the update process.
    """
    try:
        while True:
            try:
                update_repo(LOCAL_REPO_PATH)
                list_updated_files(REPO_URL)
                convert_to_elastalert_format(LOCAL_REPO_PATH, ELASTALERT_RULES_PATH)
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
    main()