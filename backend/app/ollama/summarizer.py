import logging
from app.ollama.client import generate
from app.core.exceptions import PipelineException

logger = logging.getLogger(__name__)


async def summarize(
    query: str,
    search_results: list,
    model: str
) -> str:
    logger.info(f"Summarizing {len(search_results)} search results using model '{model}'...")

    context = ""
    for result in search_results:
        title = result.get("title", "No Title")
        content = result.get("content", result.get("snippet", ""))  # handle different field mappings
        context += f"""
Başlık: {title}
İçerik: {content}

"""

    prompt = f"""
Araştırma konusu:

{query}

Kaynaklar:

{context}

Kaynakları özetle.
"""

    try:
        summary = await generate(prompt, model=model)
        if not summary or not summary.strip():
            raise ValueError("Summarizer model returned empty or whitespace response.")
        
        logger.info("Successfully generated research summary.")
        return summary
    except Exception as e:
        logger.error(f"Summarization failed during generation: {e}")
        # Make sure that if it was already a PipelineException (e.g. timeout/model not found),
        # we can bubble it up directly or wrap it. The requirement says:
        # Summarizer hatası: stage="summarizer", message="Summarization failed.", details="Model generation failed during summary stage."
        raise PipelineException(
            status_code=500,
            stage="summarizer",
            message="Summarization failed.",
            details="Model generation failed during summary stage."
        )