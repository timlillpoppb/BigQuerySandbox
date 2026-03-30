#!/usr/bin/env python3
"""
Automated PR creation, validation, and merge to master.
Uses GitHub REST API directly (no gh CLI required).
"""

import os
import sys
import time
import json
import subprocess
from typing import Optional, Dict, Any
import urllib.request
import urllib.error

# Configuration
REPO_OWNER = "timlillpoppb"
REPO_NAME = "BigQuerySandbox"
HEAD_BRANCH = "feature/bi-dashboard"
BASE_BRANCH = "master"

def get_github_token() -> str:
    """Get GitHub token from environment or prompt user."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    
    # Try to read from git config
    try:
        result = subprocess.run(
            ["git", "config", "--global", "github.token"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass
    
    print("ERROR: GITHUB_TOKEN not found in environment")
    print("Set it with: $env:GITHUB_TOKEN = 'your_token_here'")
    print("Or see: https://docs.github.com/en/authentication/keeping-your-data-secure/managing-your-personal-access-tokens")
    sys.exit(1)

def github_api_call(
    method: str,
    endpoint: str,
    headers: Dict[str, str],
    data: Optional[Dict[str, Any]] = None
) -> tuple[int, Dict[str, Any]]:
    """Make GitHub API call."""
    url = f"https://api.github.com{endpoint}"
    
    if data:
        data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            body = json.loads(response.read().decode('utf-8'))
            return response.status, body
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode('utf-8'))
        return e.code, body
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def main():
    token = get_github_token()
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    print("=== Automating PR Creation & Merge ===\n")
    
    # Step 1: Check if PR already exists
    print("[1/4] Checking for existing PR...")
    endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls?head={REPO_OWNER}:{HEAD_BRANCH}&base={BASE_BRANCH}"
    status, prs = github_api_call("GET", endpoint, headers)
    
    if status == 200 and prs:
        pr_number = prs[0]["number"]
        print(f"  PR #{pr_number} already exists")
    else:
        # Step 2: Create PR
        print("[2/4] Creating new PR...")
        endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
        pr_data = {
            "title": "Deploy: Feature BI Dashboard to Production",
            "body": """Automated PR from feature/bi-dashboard to master.

## Changes
- Streamlit dashboard fixes and navigation improvements
- dbt data pipeline updates
- Verified table existence and schema compliance

## Checklist
- [x] All changes committed to feature/bi-dashboard
- [x] dbt tests passing
- [ ] Awaiting GitHub Actions CI/CD validation

Once CI/CD checks pass, this PR will auto-merge to master and trigger production deployment.""",
            "head": f"{REPO_OWNER}:{HEAD_BRANCH}",
            "base": BASE_BRANCH,
        }
        
        status, pr = github_api_call("POST", endpoint, headers, pr_data)
        if status == 201:
            pr_number = pr["number"]
            print(f"  Created PR #{pr_number}")
        else:
            print(f"  ERROR: {pr}")
            sys.exit(1)
    
    # Step 3: Enable auto-merge
    print(f"[3/4] Enabling auto-merge for PR #{pr_number}...")
    endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/merge"
    merge_data = {
        "merge_method": "squash",
    }
    
    # Enable auto-merge (requires updated API and permissions)
    endpoint_automerge = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/auto_merge"
    automerge_data = {
        "merge_method": "squash",
        "commit_title": f"Deploy: Feature BI Dashboard",
        "commit_message": "Auto-merged to master. Production deployment will commence.",
    }
    
    status, result = github_api_call("POST", endpoint_automerge, headers, automerge_data)
    if status in [200, 201]:
        print(f"  Auto-merge enabled")
        auto_merge_enabled = True
    else:
        print(f"  Auto-merge failed (status {status}): {result}")
        print(f"  Will monitor checks and merge manually when ready")
        auto_merge_enabled = False
    
    # Step 4: Monitor CI/CD
    print(f"[4/4] Monitoring CI/CD checks...")
    print(f"\n  PR URL: https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{pr_number}")
    
    max_wait = 600  # 10 minutes
    check_interval = 10
    elapsed = 0
    
    while elapsed < max_wait:
        # Get PR status
        endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
        status, pr = github_api_call("GET", endpoint, headers)
        
        if status == 200:
            state = pr.get("state")
            merged = pr.get("merged", False)
            
            if merged:
                print(f"  [OK] PR #{pr_number} has been merged!")
                print("\n=== Deployment Complete ===")
                print("GitHub Actions is now deploying to production...")
                break
            
            # Check check runs
            endpoint_checks = f"/repos/{REPO_OWNER}/{REPO_NAME}/commits/{pr['head']['sha']}/check-runs"
            check_status, checks = github_api_call("GET", endpoint_checks, headers)
            
            if check_status == 200 and checks.get("check_runs"):
                run_statuses = [c["status"] for c in checks["check_runs"]]
                conclusion_statuses = [c.get("conclusion") for c in checks["check_runs"]]
                
                in_progress = "in_progress" in run_statuses
                all_passed = all(c == "success" for c in conclusion_statuses if c)
                any_failed = any(c == "failure" for c in conclusion_statuses if c)
                
                if in_progress:
                    print(f"  Checks in progress... ({elapsed}s)")
                elif all_passed:
                    print(f"  [OK] All checks passed!")
                    if not auto_merge_enabled:
                        # Try to merge the PR manually
                        print(f"  Merging PR #{pr_number}...")
                        merge_endpoint = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/merge"
                        merge_data = {
                            "merge_method": "squash",
                            "commit_title": f"Deploy: Feature BI Dashboard",
                            "commit_message": "Merged to master. Production deployment will commence.",
                        }
                        merge_status, merge_result = github_api_call("PUT", merge_endpoint, headers, merge_data)
                        if merge_status == 200:
                            print(f"  [OK] PR #{pr_number} merged successfully!")
                            print("\n=== Deployment Complete ===")
                            print("GitHub Actions is now deploying to production...")
                            break
                        else:
                            print(f"  [FAIL] Failed to merge PR (status {merge_status}): {merge_result}")
                            print(f"  Please merge manually: https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{pr_number}")
                            break
                elif any_failed:
                    print(f"  [FAIL] Some checks failed. See PR for details.")
                    print(f"  URL: https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{pr_number}")
                    break
        
        time.sleep(check_interval)
        elapsed += check_interval
    
    if elapsed >= max_wait:
        print(f"\n  Timeout reached. Check PR status manually:")
        print(f"  https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{pr_number}")
    
    print("\n[Done] Next step: Monitor GitHub Actions CD workflow for production deployment")

if __name__ == "__main__":
    main()
