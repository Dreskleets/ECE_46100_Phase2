import os
import requests
import logging
import base64

logger = logging.getLogger(__name__)

class GitHubAPI:
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        else:
            logger.warning("GITHUB_TOKEN not found. API rate limits will be low.")

    def _get(self, url: str, params: dict = None) -> requests.Response:
        try:
            return requests.get(url, headers=self.headers, params=params, timeout=10)
        except requests.RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            return requests.Response() # Empty response

    def get_repo_info(self, owner: str, repo: str) -> dict | None:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = self._get(url)
        if response.status_code == 200:
            return response.json()
        logger.error(f"Failed to get repo info for {owner}/{repo}: {response.status_code}")
        return None

    def get_contributors(self, owner: str, repo: str) -> list[dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
        response = self._get(url, params={"per_page": 100})
        if response.status_code == 200:
            return response.json()
        return []

    def get_commits(self, owner: str, repo: str) -> list[dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        response = self._get(url, params={"per_page": 100})
        if response.status_code == 200:
            return response.json()
        return []

    def get_license(self, owner: str, repo: str) -> dict | None:
        url = f"https://api.github.com/repos/{owner}/{repo}/license"
        response = self._get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def get_readme(self, owner: str, repo: str) -> str | None:
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        response = self._get(url)
        if response.status_code == 200:
            content = response.json().get("content", "")
            try:
                return base64.b64decode(content).decode("utf-8")
            except Exception:
                return None
        return None

    def get_issues(self, owner: str, repo: str, state: str = "all") -> list[dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        response = self._get(url, params={"state": state, "per_page": 100})
        if response.status_code == 200:
            return response.json()
        return []

    def get_contents(self, owner: str, repo: str, path: str = "") -> list[dict] | dict | None:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        response = self._get(url)
        if response.status_code == 200:
            return response.json()
        return None
