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
                        "5. The role of the country in the query.\n"
                        "6. The countries explicitly named as subjects of a comparison, if any.\n\n"
                        "Trade intent rules:\n\n"
                        "- COMPARISON:\n"
                        "  The user wants to compare two explicitly named countries for the same product/trade context.\n"
                        "  Examples:\n"
                        "  'Compare Germany and United Arab Emirates for electrical panels to India'\n"
                        "  'Which is a better supplier, Germany or United Arab Emirates, for electrical panels to India?'\n"
                        "  Set comparison_country_texts to the explicitly named comparison countries.\n"
                        "  Do not put comparison countries into country_text unless one of them is also the trade destination, origin, or location.\n\n"
                        "- SUPPLIER_SEARCH:\n"
                        "  The user wants to find countries that "
                        "supply a product, or suppliers/buyers in a "
                        "specified location.\n"
                        "  Examples:\n"
                        "  'Find suppliers of electrical panels'\n"
                        "  'Find suppliers of electrical panels in India'\n"
                        "  'Find suppliers of electrical panels to India'\n\n"
                        "- BUYER_SEARCH:\n"
                        "  The user wants to find countries that "
                        "buy or import a product, or buyers/importers "
                        "in a specified location.\n"
                        "  Examples:\n"
                        "  'Who buys electrical panels from India?'\n"
                        "  'Who imports electrical panels in India?'\n"
                        "  'Find buyers of electrical panels in India'\n\n"
                        "- EXPORT_OPPORTUNITY:\n"
                        "  The user wants to identify countries "
                        "that may be good target markets for "
                        "exporting a product from a specified "
                        "origin country.\n"
                        "  Example: 'Which countries should I "
                        "target for exporting electrical panels "
                        "from India?'\n"
                        "  The mentioned country is normally the "
                        "origin/exporting country.\n\n"
                        "- IMPORT_OPPORTUNITY:\n"
                        "  The user wants to identify countries "
                        "that may be good source markets for "
                        "importing a product into a specified "
                        "destination country.\n"
                        "  Example: 'Which countries should India "
                        "source electrical panels from?'\n"
                        "  The mentioned country is normally the "
                        "destination/importing country.\n\n"
                        "Country role rules:\n\n"
                        "- LOCATION:\n"
                        "  The country is the physical or commercial "
                        "location of the suppliers or buyers/importers.\n"
                        "  Use LOCATION when the query uses wording "
                        "such as 'in <country>', 'located in <country>', "
                        "'based in <country>', or otherwise clearly "
                        "indicates that suppliers or buyers are located "
                        "there.\n"
                        "  Examples:\n"
                        "  'Find suppliers of electrical panels in India'\n"
                        "  'Who imports electrical panels in India?'\n"
                        "  'Find buyers of electrical panels in India'\n"
                        "  In these examples, India is the LOCATION.\n\n"
                        "- DESTINATION:\n"
                        "  The country is where the goods are going "
                        "to or being imported into.\n"
                        "  Use DESTINATION when wording such as "
                        "'to <country>', 'into <country>', or an "
                        "equivalent destination relationship is used.\n"
                        "  Example:\n"
                        "  'Find suppliers of electrical panels to India'\n"
                        "  Here India is the destination.\n\n"
                        "- ORIGIN:\n"
                        "  The country is where the goods are coming "
                        "from or being exported from.\n"
                        "  Use ORIGIN when wording such as "
                        "'from <country>', 'exported from <country>', "
                        "or an equivalent origin relationship is used.\n"
                        "  Examples:\n"
                        "  'Who buys electrical panels from India?'\n"
                        "  'Which countries should I target for "
                        "exporting electrical panels from India?'\n"
                        "  Here India is the origin.\n\n"
                        "- UNSPECIFIED:\n"
                        "  Use UNSPECIFIED when no country is mentioned.\n\n"
                        "Important disambiguation rules:\n"
                        "1. For supplier or buyer searches, 'in <country>' "
                        "means the suppliers or buyers are located in "
                        "that country, so use LOCATION.\n"
                        "2. 'to <country>' means goods are going to that "
                        "country, so use DESTINATION.\n"
                        "3. 'from <country>' means goods are coming from "
                        "that country, so use ORIGIN.\n"
                        "4. Do not infer DESTINATION or ORIGIN merely "
                        "because the query contains an import/export "
                        "verb. Pay attention to the grammatical "
                        "relationship between the country and the goods.\n"
                        "5. For example, 'Who imports electrical panels "
                        "in India?' means importers located in India, "
                        "therefore LOCATION.\n\n"
                        "For COMPARISON queries, extract all explicitly named comparison countries in comparison_country_texts.\n"
                        "For non-comparison queries, leave comparison_country_texts empty.\n\n"
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
