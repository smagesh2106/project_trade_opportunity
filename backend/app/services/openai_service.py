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
                        "of a Trade Opportunity Explorer.\n\n"
                        "Extract:\n"
                        "1. The user's trade-related intent.\n"
                        "2. The product being requested.\n"
                        "3. The country mentioned, if any.\n"
                        "4. Whether the query applies to all "
                        "countries or a specific country.\n"
                        "5. The role of the country in the query.\n\n"
                        "Country role rules:\n\n"
                        "- LOCATION:\n"
                        "  The country is where the suppliers or "
                        "buyers are located.\n"
                        "  Example: "
                        "'Find suppliers of electrical panels "
                        "in India'\n"
                        "  Here India is the supplier location.\n\n"
                        "- DESTINATION:\n"
                        "  The country is where the goods are "
                        "going to / being imported into.\n"
                        "  Example: "
                        "'Find suppliers of electrical panels "
                        "to India'\n"
                        "  Here India is the destination/importing "
                        "country.\n\n"
                        "- ORIGIN:\n"
                        "  The country is where the goods are "
                        "coming from / being exported from.\n"
                        "  Example: "
                        "'Find buyers of electrical panels "
                        "from India'\n"
                        "  Here India is the origin/exporting "
                        "country.\n\n"
                        "- UNSPECIFIED:\n"
                        "  No country is mentioned.\n"
                        "  Example: "
                        "'Find suppliers of electrical panels'\n\n"
                        "Important:\n"
                        "Do not interpret 'in' as 'to'.\n"
                        "Do not interpret 'to' as 'in'.\n"
                        "Do not interpret 'from' as 'in'.\n"
                        "Preserve the semantic role expressed "
                        "by the user's wording.\n\n"
                        "If a product or country is not present, "
                        "return null for that field.\n"
                        "Do not invent information."
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
