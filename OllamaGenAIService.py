from ollama import chat
from GenAIService import GenAIService

class OllamaGenAIService(GenAIService):
    """
    Ollama-based implementation of the GenAIService interface.
    """

    def __init__(self, model: str):
        """
        Initializes the Ollama service with the specified model.

        Args:
            model: The name of the Ollama model to use (e.g., 'gemma3:12b').
        """
        self._model = model

    def get_column_name(self, column_list: list[str], required_column_description: str) -> str:
        concatenated_column_list = ",".join(column_list)
        messages = [
            {
                'role': 'user',
                'content': f"Among these columns in a credit card/banking statement, which one refers to the one with the '{required_column_description}'? {concatenated_column_list}. Just list the name of the column.",
            },
        ]

        response = chat(self._model, messages=messages)
        column_name = response['message']['content'].strip()
        return column_name

    def categorize_expense(self, description: str, amount: float) -> str:
        messages = [
            {
                'role': 'system',
                'content': "You are a budgeting consultant. You are helping the user categorize financial transactions from bank statements or credit cards, into one of these categories: Accommodation, Transport, Meals, Groceries, Airfare, Subscriptions, Recurring Payments, Other. Negative amounts indicate payments, and positive amounts indicate refunds or credits. Print only the category of the transaction and nothing else. Pay special attention to the description, if you find full or partial names of airline companies and larger expense amounts (say double digits to hundreds of dollars), then it is likely Airfare.",
            },
            {
                'role': 'user',
                'content': f"Description: '{description}', amount: {amount}",
            },
        ]

        response = chat(self._model, messages=messages)
        category = response['message']['content'].strip()
        return category