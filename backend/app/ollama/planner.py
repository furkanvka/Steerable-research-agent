import json
import logging
from app.ollama.client import generate
from app.core.exceptions import PipelineException

logger = logging.getLogger(__name__)


async def create_plan(query: str, model: str) -> list[str]:
    prompt = f"""
Kullanıcının araştırma konusu:

{query}

Araştırmayı 3-5 alt başlığa ayır.

Sadece JSON listesi döndür.

Örnek:

[
    "başlık1",
    "başlık2"
]
"""

    logger.info("Requesting plan from Ollama...")
    response = await generate(prompt, model=model)
    logger.debug(f"Planner response received: {response}")

    try:
        # Strip potential markdown formatting codeblocks if the LLM outputted them
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        plan = json.loads(cleaned_response)
        if not isinstance(plan, list):
            raise ValueError("Planner response is not a list")
        plan = [str(item).strip() for item in plan if item]
        if not plan:
            raise ValueError("Planner returned an empty list of topics")
        
        logger.info(f"Successfully generated plan with {len(plan)} topics: {plan}")
        return plan
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Planner JSON parse error. Original response: {response}. Error: {e}")
        raise PipelineException(
            status_code=500,
            stage="planner",
            message="Planner returned invalid JSON.",
            details="The model response could not be parsed into a task list."
        )