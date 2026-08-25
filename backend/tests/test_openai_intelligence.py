from app.services.openai_service import OpenAIService


def test_query(query: str):
    service = OpenAIService()

    result = service.understand_query(query)

    print("\nQuery:")
    print(f"  {query}")

    print(f"Intent: " f"{result.intent.value}")

    print(f"Product: " f"{result.product_text}")

    print(f"Country: " f"{result.country_text}")

    print(f"Country scope: " f"{result.country_scope.value}")

    print(f"Country role: " f"{result.country_role.value}")


if __name__ == "__main__":

    test_query("Find suppliers of electrical panels in India")

    test_query("Find suppliers of electrical panels to India")

    test_query("Find buyers of electrical panels from India")

    test_query("Find suppliers of electrical panels")
