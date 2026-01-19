from datetime import datetime
from abc import ABC, abstractmethod
import dateutil.parser as date_parser

class Logger(ABC):
    """
    Abstract base class for loggers. Defines the interface for logging transactions and expenses.
    """

    @abstractmethod
    def log_transaction(self, date, description, amount, category, status, sub_status=None):
        """Logs a single transaction."""
        pass

    @abstractmethod
    def log_finalized_transaction(self, date, description, amount):
        """Logs a finalized transaction."""
        pass

    @abstractmethod
    def print_expenses_by_category(self, all_expenses):
        """Prints expenses grouped by category."""
        pass
    
    @abstractmethod
    def calculate_and_print_total_expenses_by_category(self, all_expenses):
        """Calculates and prints total expenses grouped by category."""
        pass

    @abstractmethod
    def log_info(self, log):
        """Logs an informational message."""
        pass

class ConsoleLogger(Logger):
    """
    Concrete implementation of the Logger interface that logs to the console.
    """

    def log_transaction(self, date, description, amount, category, status, sub_status=None):
        """Logs a single transaction to the console."""
        log_message = f"{date.strftime('%Y-%m-%d')}|{description}|${amount:.2f}|{category}|{status}"
        if sub_status:
            log_message += f"|{sub_status}"
        print(log_message)

    def log_finalized_transaction(self, date, description, amount):
        """Logs a finalized transaction to the console."""
        log_entry = f"{date.strftime('%Y-%m-%d')}|{description}|${amount:.2f}"
        print(log_entry)

    def print_expenses_by_category(self, all_expenses):
        """Prints expenses grouped by category to the console."""
        categories = sorted(list(set([expense['category'] for expense in all_expenses])))

        print("-" * 20)
        print("-" * 20)
        for category in categories:
            expenses_in_category = sorted([expense for expense in all_expenses if expense['category'] == category], key=lambda x: date_parser.parse(x['date']).strftime('%Y-%m-%d'))
            print(f"Category: {category}")
            print("-" * 20)
            for expense in expenses_in_category:
                self.log_finalized_transaction(date_parser.parse(expense['date']), expense['description'], expense['amount'])
            total = sum(e['amount'] for e in expenses_in_category)
            print(f"  Total: ${total:.2f}")
            print("-" * 20)

    def calculate_and_print_total_expenses_by_category(self, all_expenses):
        # Group expenses by category and calculate sums
        categorized_expenses = {}
        for expense in all_expenses:
            category = expense['category']
            if category not in categorized_expenses:
                categorized_expenses[category] = 0
            categorized_expenses[category] += round(expense['amount'],2)

        # Calculate total trip expenditure
        total_expenditure = sum(categorized_expenses.values())
        
        self.log_info("Categorized Expenses:")
        self.log_info({category: round(amount, 2) for category, amount in categorized_expenses.items()})
        self.log_info("\nTotal Expenditure: " + str(total_expenditure))

        return categorized_expenses, total_expenditure

    def log_info(self, log):
        """Logs an informational message to the console."""
        print(log)