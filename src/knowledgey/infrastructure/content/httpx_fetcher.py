import httpx

from knowledgey.application.ports import FetchError

USER_AGENT = "knowledgey/0.1"


class HttpxFetcher:
    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    def fetch(self, url: str) -> str:
        try:
            response = httpx.get(
                url,
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            )

            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FetchError(f"could not fetch {url}: {exc}") from exc
        return response.text
