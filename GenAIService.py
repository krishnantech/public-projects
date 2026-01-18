from abc import ABC, abstractmethod

class GenAIService(ABC):
    """
    Abstract base class defining the interface for AI-powered expense analysis services.
    """

    @abstractmethod
    def get_column_name(self, column_list: list[str], column_description: str) -> str:
        """
        Given a list of column names and a required column description,
        returns the column name that best aligns with the description.

        Args:
            column_list: List of column names from the CSV file.
            column_description: Description of the column that helps identify the best matching column from column_list.

        Returns:
            The column name that best aligns with the description.
        """
        pass

    @abstractmethod
    def categorize_expense(self, description: str, amount: float) -> str:
        """
        Categorizes an expense based on its description and amount.

        Args:
            description: The transaction description.
            amount: The transaction amount.

        Returns:
            The category of the expense.
        """
        pass