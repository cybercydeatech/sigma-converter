import os
import subprocess
from git import Repo
import ruamel.yaml
import requests


# Constants
SIGMA_REPO_URL = 'https://github.com/SigmaHQ/sigma.git'
SIGMA_REPO_DIR = 'sigma_repo'
ELASTALERT_RULES_DIR = 'elastalert_rules'
MODIFIED_RULES_DIR = 'modified_rules'

def clone_repo(repo_url, repo_dir):
    if os.path.exists(repo_dir):
        repo = Repo(repo_dir)
        repo.remote().pull()
    else:
        Repo.clone_from(repo_url, repo_dir)

def convert_sigma_to_elastalert():
    os.makedirs(ELASTALERT_RULES_DIR, exist_ok=True)
    sigma_rules_path = os.path.join(SIGMA_REPO_DIR, 'rules')
    for root, _, files in os.walk(sigma_rules_path):
        for file in files:
            if file.endswith('.yml'):
                sigma_rule = os.path.join(root, file)
                elastalert_rule = os.path.join(ELASTALERT_RULES_DIR, file)
                subprocess.run(['/home/rafiq/sigma/tools/sigmac', '-t', 'elastalert', '-c', 'sigmac_config.yml', sigma_rule, '-o', elastalert_rule])

def convert_sigma_to_elastalert():
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
    os.makedirs(MODIFIED_RULES_DIR, exist_ok=True)
    for root, _, files in os.walk(ELASTALERT_RULES_DIR):
        for file in files:
            if file.endswith('.yml'):
                elastalert_rule = os.path.join(root, file)
                modified_rule = os.path.join(MODIFIED_RULES_DIR, file)
                with open(elastalert_rule, 'r') as f:
                    content = f.read()
                # Apply necessary changes to the content
                modified_content = content.replace('old_value', 'new_value')
                with open(modified_rule, 'w') as f:
                    f.write(modified_content)

def main():
    clone_repo(SIGMA_REPO_URL, SIGMA_REPO_DIR)
    convert_sigma_to_elastalert()
    modify_elastalert_rules()

if __name__ == '__main__':
    main()