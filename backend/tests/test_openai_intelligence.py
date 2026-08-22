from app.services.openai_service import OpenAIService


def test_query_understanding():
    service = OpenAIService()

    query = "I'm looking for suppliers of electrical panels in India."
    # query = "Find suppliers of electrical panels."

    result = service.understand_query(query)

    print("Intent:", result.intent)
    print("Intent 2:", result.intent.value)
    print("Product:", result.product_text)
    print("Country:", result.country_text)
    print("Country Scope:", result.country_scope.value)


if __name__ == "__main__":
    test_query_understanding()
