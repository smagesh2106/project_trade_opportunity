from openai import OpenAI

from app.core.config import settings
from app.schemas.intelligence import QueryUnderstanding


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key,
        )
        self.model = settings.openai_model

    def understand_query(
        self,
        query: str,
    ) -> QueryUnderstanding:

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are the query understanding component "
                        "of a Trade Opportunity Explorer. "
                        "Extract the user's trade-related intent, "
                        "product description, and country. "
                        "Do not invent information. "
                        "If something is not present, return null."
                    ),
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
            text_format=QueryUnderstanding,
        )

        return response.output_parsed
