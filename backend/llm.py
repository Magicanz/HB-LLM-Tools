import os
from google import genai
from google.genai.types import GenerateContentResponse
from pydantic import BaseModel


# Process AI response to structure recognized items and locations
def get_response(prompt: str, llm_config: dict = None) -> GenerateContentResponse:
    if llm_config is None:
        llm_config = {
            "response_mime_type": "application/json"
        }

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=llm_config
    )

    return response


def get_parsed_list(prompt: str, llm_config: dict = None) -> list[dict]:
    return [item.model_dump() for item in get_response(prompt, llm_config).parsed]