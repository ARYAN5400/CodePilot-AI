import httpx

API = "https://api.github.com"

class GitHubError(Exception):
    pass

class GitHubClient:
    def __init__(self, token: str):
        self._client = httpx.AsyncClient(
            base_url=API, timeout=httpx.Timeout(12.0),
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2026-03-10"},
            follow_redirects=False,
        )

    async def _get(self, path: str):
        response = await self._client.get(path)
        if response.is_error:
            raise GitHubError("GitHub request could not be completed")
        return response.json()

    async def identity(self) -> dict:
        data = await self._get("/user")
        return {"login": data["login"], "avatar_url": data.get("avatar_url"), "html_url": data.get("html_url")}

    async def repositories(self) -> list[dict]:
        data = await self._get("/user/repos?visibility=all&affiliation=owner,collaborator,organization_member&sort=updated&per_page=100")
        return [{"id": repo["id"], "name": repo["name"], "full_name": repo["full_name"], "private": repo["private"], "html_url": repo["html_url"], "default_branch": repo.get("default_branch")} for repo in data if not repo.get("fork", False)]

    async def close(self):
        await self._client.aclose()
