import httpx
from urllib.parse import quote
from .credential_store import store_credential, get_credential

GITHUB_API_BASE = "https://api.github.com"

def get_github_headers() -> dict:
    token = get_credential("github", "token")
    if not token:
        raise ValueError("GitHub token is invalid or expired, please reconnect")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def validate_and_store_token(token: str) -> bool:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        resp = httpx.get(f"{GITHUB_API_BASE}/user", headers=headers, timeout=30.0)
        if resp.status_code == 200:
            store_credential("github", "token", token)
            return True
        return False
    except httpx.RequestError:
        return False

def _handle_response(resp: httpx.Response):
    if resp.status_code in (401, 403):
        raise ValueError("GitHub token is invalid or expired, please reconnect")
    resp.raise_for_status()
    return resp.json()

def list_repos() -> list[dict]:
    headers = get_github_headers()
    resp = httpx.get(f"{GITHUB_API_BASE}/user/repos?sort=updated&per_page=100", headers=headers, timeout=30.0)
    data = _handle_response(resp)
    
    results = []
    for repo in data:
        results.append({
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stargazers_count": repo.get("stargazers_count"),
            "updated_at": repo.get("updated_at")
        })
    return results

def list_issues(repo: str, state: str = "open") -> list[dict]:
    headers = get_github_headers()
    safe_repo = quote(repo, safe="")
    safe_state = quote(state, safe="")
    resp = httpx.get(f"{GITHUB_API_BASE}/repos/{safe_repo}/issues?state={safe_state}&per_page=100", headers=headers, timeout=30.0)
    data = _handle_response(resp)
    
    results = []
    for issue in data:
        if "pull_request" in issue:
            continue
        results.append({
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "labels": [lbl.get("name") for lbl in issue.get("labels", [])],
            "created_at": issue.get("created_at"),
            "html_url": issue.get("html_url")
        })
    return results

def search_issues(query: str) -> list[dict]:
    headers = get_github_headers()
    safe_q = quote(query, safe="")
    resp = httpx.get(f"{GITHUB_API_BASE}/search/issues?q={safe_q}", headers=headers, timeout=30.0)
    data = _handle_response(resp)
    
    results = []
    for issue in data.get("items", []):
        results.append({
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "labels": [lbl.get("name") for lbl in issue.get("labels", [])],
            "created_at": issue.get("created_at"),
            "html_url": issue.get("html_url")
        })
    return results

def create_issue(repo: str, title: str, body: str = "") -> bool:
    headers = get_github_headers()
    payload = {
        "title": title,
        "body": body
    }
    resp = httpx.post(f"{GITHUB_API_BASE}/repos/{repo}/issues", headers=headers, json=payload, timeout=30.0)
    _handle_response(resp)
    return True

def list_pull_requests(repo: str, state: str = "open") -> list[dict]:
    headers = get_github_headers()
    safe_repo = quote(repo, safe="")
    safe_state = quote(state, safe="")
    resp = httpx.get(f"{GITHUB_API_BASE}/repos/{safe_repo}/pulls?state={safe_state}&per_page=100", headers=headers, timeout=30.0)
    data = _handle_response(resp)
    
    results = []
    for pr in data:
        results.append({
            "number": pr.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "html_url": pr.get("html_url")
        })
    return results

def get_pr_status(repo: str, pr_number: int) -> dict:
    headers = get_github_headers()
    safe_repo = quote(repo, safe="")
    safe_pr = quote(str(pr_number), safe="")
    pr_resp = httpx.get(f"{GITHUB_API_BASE}/repos/{safe_repo}/pulls/{safe_pr}", headers=headers, timeout=30.0)
    pr_data = _handle_response(pr_resp)
    head_sha = pr_data.get("head", {}).get("sha")
    
    if not head_sha:
        raise ValueError("Could not find head sha for PR")
        
    status_resp = httpx.get(f"{GITHUB_API_BASE}/repos/{safe_repo}/commits/{head_sha}/status", headers=headers, timeout=30.0)
    status_data = _handle_response(status_resp)
    
    return {
        "state": status_data.get("state"),
        "total_count": status_data.get("total_count"),
        "statuses": [
            {
                "context": s.get("context"),
                "state": s.get("state"),
                "description": s.get("description"),
                "target_url": s.get("target_url")
            } for s in status_data.get("statuses", [])
        ]
    }

def search_code(query: str, repo: str | None = None) -> list[dict]:
    headers = get_github_headers()
    q = query
    if repo:
        q = f"{query} repo:{repo}"
    safe_q = quote(q, safe="")
    resp = httpx.get(f"{GITHUB_API_BASE}/search/code?q={safe_q}", headers=headers, timeout=30.0)
    data = _handle_response(resp)
    
    results = []
    for item in data.get("items", []):
        results.append({
            "name": item.get("name"),
            "path": item.get("path"),
            "repo": item.get("repository", {}).get("full_name"),
            "html_url": item.get("html_url")
        })
    return results
