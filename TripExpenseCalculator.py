from ollama import chat
import pandas as pd
from datetime import datetime, timedelta

def analyze_trip_expenses(start_date, end_date, location, accommodation, csv_files):
    """
    Analyzes trip expenses from financial statements using a local AI model.

    Args:
        start_date (str): Start date of the trip (YYYY-MM-DD).
        end_date (str): End date of the trip (YYYY-MM-DD).
        location (str): Location of the trip.
        accommodation (str): Type of accommodation (hotel, resort, cruise, etc.).
        csv_files (list): List of paths to CSV files containing financial statements.

    Returns:
        dict: A dictionary containing categorized expenses and total trip expenditure.
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    advance_booking_months = 1  # Check for advance bookings up to 1 month prior

    all_expenses = []

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        # Assuming CSV has columns: 'date', 'description', 'amount'
        df['date'] = pd.to_datetime(df['date'])

        for index, row in df.iterrows():
            transaction_date = row['date']
            description = row['description']
            amount = row['amount']

            # Filter transactions within the trip dates or for advance bookings
            if transaction_date >= start_date and transaction_date <= end_date:
                # Categorize expenses
                category = categorize_expense(description, location)
                all_expenses.append({'date': transaction_date, 'description': description, 'amount': amount, 'category': category})
            elif transaction_date >= (start_date - timedelta(days=advance_booking_months * 1)) and transaction_date <= (start_date - timedelta(days=1)):
                # Categorize expenses for advance bookings
                category = categorize_expense(description, location)
                all_expenses.append({'date': transaction_date, 'description': description, 'amount': amount, 'category': category})

    # Group expenses by category and calculate sums
    categorized_expenses = {}
    for expense in all_expenses:
        category = expense['category']
        if category not in categorized_expenses:
            categorized_expenses[category] = 0
        categorized_expenses[category] += expense['amount']

    # Calculate total trip expenditure
    total_expenditure = sum(categorized_expenses.values())

    return categorized_expenses, total_expenditure

def categorize_expense(description, location):
    """
    Categorizes an expense based on its description and location.
    Uses Ollama to categorize expenses.
    """
    messages = [
        {
            'role': 'user',
            'content': f"Categorize the following expense description: '{description}' for a trip to {location}. Possible categories are: Accommodation, Transport, Meals, Tours, Groceries, Other.",
        },
    ]
    response = chat('gemma3', messages=messages)
    category = response['message']['content'].strip()
    return category


# Example invocation
if __name__ == "__main__":
    start_date = "2025-12-20"
    end_date = "2025-12-27"
    location = "New York"
    accommodation = "Hotel"
    csv_files = ["C:\\data\\bank_statement.csv", "C:\\data\\credit_card_statement.csv"]

    categorized_expenses, total_expenditure = analyze_trip_expenses(start_date, end_date, location, accommodation, csv_files)

    print("Categorized Expenses:")
    print(categorized_expenses)
    print("\nTotal Expenditure:", total_expenditure)