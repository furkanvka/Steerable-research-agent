import httpx
import logging

from app.core.config import settings
from app.core.exceptions import PipelineException

logger = logging.getLogger(__name__)


async def search(query: str):
    url = f"{settings.SEARXNG_URL}/search"
    logger.info(f"Searching SearXNG at {url} for query: '{query}'")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={
                    "q": query,
                    "format": "json"
                },
                timeout=15.0  # 15 seconds search timeout
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])[:5]
            logger.info(f"SearXNG query '{query}' returned {len(results)} results.")
            return results
    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to SearXNG at {settings.SEARXNG_URL}: {e}")
        raise PipelineException(
            status_code=502,
            stage="search",
            message="Could not connect to SearXNG.",
            details=f"{settings.SEARXNG_URL} is unreachable."
        )
    except httpx.TimeoutException as e:
        logger.error(f"Timeout occurred during SearXNG query '{query}': {e}")
        raise PipelineException(
            status_code=504,
            stage="search",
            message="Search request timed out.",
            details="SearXNG query request exceeded the configured timeout."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"SearXNG HTTP error status {e.response.status_code}: {e.response.text}")
        raise PipelineException(
            status_code=e.response.status_code,
            stage="search",
            message="SearXNG returned an HTTP error.",
            details=f"Status code: {e.response.status_code}, response: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during SearXNG query '{query}': {e}")
        raise PipelineException(
            status_code=500,
            stage="search",
            message="An unexpected error occurred with SearXNG.",
            details=str(e)
        )