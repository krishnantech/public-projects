from abc import ABC, abstractmethod

class OutputWriter(ABC):
    """
    Generic interface for writing expense data.
    """
    @abstractmethod
    def write_expenses(self, all_expenses, categorized_expenses, total_expenditure):
        """
        Writes categorized expenses and total expenditure to an output format.

        Args:
            all_expenses (list): A list of all expense dictionaries with date, description, amount, and category.
            categorized_expenses (dict): A dictionary of category totals.
            total_expenditure (float): The total trip expenditure.
        """
        pass
