import httpx
import logging

from app.core.config import settings
from app.core.exceptions import PipelineException

logger = logging.getLogger(__name__)


async def generate(prompt: str, model: str | None = None) -> str:
    if model is None:
        model = settings.OLLAMA_MODEL

    url = f"{settings.OLLAMA_URL}/api/generate"
    logger.info(f"Generating prompt using Ollama model '{model}' at {url}...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=300.0  # 90 seconds timeout for local LLM generation
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]
    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to Ollama server at {settings.OLLAMA_URL}: {e}")
        raise PipelineException(
            status_code=502,
            stage="ollama",
            message="Could not connect to Ollama server.",
            details=f"{settings.OLLAMA_URL} is unreachable."
        )
    except httpx.TimeoutException as e:
        logger.error(f"Timeout occurred while waiting for Ollama response: {e}")
        raise PipelineException(
            status_code=504,
            stage="ollama",
            message="Model request timed out.",
            details="Generation exceeded the configured timeout."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama returned HTTP error status {e.response.status_code}: {e.response.text}")
        if e.response.status_code == 404:
            raise PipelineException(
                status_code=404,
                stage="ollama",
                message="Requested model not found.",
                details=f"Install the model first using: ollama pull {model}"
            )
        else:
            raise PipelineException(
                status_code=e.response.status_code,
                stage="ollama",
                message="Ollama returned an HTTP error.",
                details=f"Status code: {e.response.status_code}, response: {e.response.text}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in Ollama generate: {e}")
        raise PipelineException(
            status_code=500,
            stage="ollama",
            message="An unexpected error occurred with Ollama.",
            details=str(e)
        )


async def get_models() -> list[str]:
    url = f"{settings.OLLAMA_URL}/api/tags"
    logger.info(f"Fetching models from Ollama at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to Ollama server at {settings.OLLAMA_URL} to fetch models: {e}")
        raise PipelineException(
            status_code=502,
            stage="ollama",
            message="Could not connect to Ollama server.",
            details=f"{settings.OLLAMA_URL} is unreachable."
        )
    except httpx.TimeoutException as e:
        logger.error(f"Timeout occurred while fetching models from Ollama: {e}")
        raise PipelineException(
            status_code=504,
            stage="ollama",
            message="Model request timed out.",
            details="Model fetch exceeded the configured timeout."
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching models from Ollama: {e}")
        raise PipelineException(
            status_code=500,
            stage="ollama",
            message="An unexpected error occurred with Ollama.",
            details=str(e)
        )