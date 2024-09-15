import json
import subprocess
import tempfile
import os

def run_bandit_on_code(code):
    # Create a temporary file to hold the code
    with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
        temp_file.write(code.encode())
        temp_file_path = temp_file.name
    
    try:
        result = subprocess.run(['bandit', '-r', temp_file_path, '-f', 'json'], capture_output=True, text=True)
        if result is None:
            return "error", "none type"
        if result.returncode == 0: 
            return "safe", "0", ""
        if result.returncode == 1:
            bandit_result = json.loads(result.stdout)
            
            cwe_codes = []
            issue_texts = []
            
            for issue in bandit_result.get("results", []):
                cwe_id = issue.get("issue_cwe", {}).get("id")
                if cwe_id:
                    cwe_code = f"CWE-{cwe_id}"
                    cwe_codes.append(cwe_code)
                    
                issue_text = issue.get("issue_text", "")
                issue_texts.append(issue_text)
            
            # Join all CWE codes and issue texts into a single string if there are multiple
            all_cwe_codes = ', '.join(cwe_codes) if cwe_codes else "none"
            all_issue_texts = ' | '.join(issue_texts) if issue_texts else "none"
            
            return "vulnerable", all_cwe_codes, all_issue_texts
        else:
            return "error", "", result.stderr
    finally:
        # Clean up temporary file
        os.remove(temp_file_path)

def process_jsonl(input_file, output_file):
    results = {}
    
    with open(input_file, 'r') as infile:
        for line in infile:
            entry = json.loads(line)
            code_id = entry['ID']
            code = entry['code']
            
            (bandit_result, cwe_code, issue_text)= run_bandit_on_code(code)
            
            results[code_id]={}
            results[code_id]["result"] = bandit_result
            results[code_id]["cwe_code"] = cwe_code
            results[code_id]["issue_text"] = issue_text
    # Save results to output JSON file
    with open(output_file, 'w') as outfile:
        json.dump(results, outfile, indent=4)

process_jsonl('./results.json', './results_evaluation.json')
