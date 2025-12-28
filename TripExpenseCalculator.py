from ollama import chat
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser

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
    advance_booking_months = 3  # Check for advance bookings up to 1 month prior

    all_expenses = []

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)

        columnListFromCsv = df.columns.tolist()
        
        # Identify relevant date, description and amount columns
        date_column = get_column_name(columnListFromCsv, "transaction date")
        description_column = get_column_name(columnListFromCsv, "name of the merchant")
        amount_column = get_column_name(columnListFromCsv, "transaction amount")

        print(f"Using columns - Date: {date_column}, Description: {description_column}, Amount: {amount_column}")

        # Assuming CSV has columns: 'date', 'description', 'amount'
        df['date'] = pd.to_datetime(df[date_column])

        for index, row in df.iterrows():
            transaction_date = row[date_column]
            description = row[description_column]
            amount = row[amount_column]           
            transaction_date_parsed = parser.parse(transaction_date) 
            category = "Other"

            # Filter transactions within the trip dates or for advance bookings
            if transaction_date_parsed >= start_date and transaction_date_parsed <= end_date:
                # Categorize expenses
                category = categorize_expense(description, location, amount)

            elif transaction_date_parsed >= (start_date - timedelta(days=advance_booking_months * 30)) and transaction_date_parsed <= (start_date - timedelta(days=1)):
                # Categorize expenses for advance bookings. We will look for specific types here (airfare, accommodation)
                category = categorize_expense(description, location, amount)

                if(category not in ["Airfare", "Accommodation"]):
                    #log_transaction(transaction_date_parsed, description, amount, category, status="Ignored", sub_status="Older irrelevant transaction")
                    continue  

            else:
                # Ignore transactions outside the trip date range and advance booking window
                continue
    
            # ignore subscriptions and recurring payments
            if (category not in ["Subscriptions", "Recurring Payments"]):
                log_transaction(transaction_date_parsed, description, amount, category, status="Accepted")
                all_expenses.append({'date': transaction_date, 'description': description, 'amount': amount, 'category': category})
            #else:
                #log_transaction(transaction_date_parsed, description, amount, category, status="Ignored", sub_status="Subscription/Recurring Payment")

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

def log_transaction(transaction_date, description, amount, category, status, sub_status=None):
    """
    Logs a bank account/credit card statement transaction.

    Args:
        transaction_date (datetime): The date of the transaction.
        description (str): The description of the transaction.
        amount (float): The amount of the transaction.
        category (str): The category of the transaction.
        status (str): The status of the transaction ('Accepted' or 'Ignored').
        sub_status (str, optional): A sub-status if the transaction is ignored. Defaults to None.
    """

    log_entry = f"{transaction_date.strftime('%Y-%m-%d')}|{description}|{amount}|{category}|{status}"
    if sub_status:
        log_entry += f"|{sub_status}"

    print(log_entry)

def categorize_expense(description, location, amount):
    """
    Categorizes an expense based on its description and location.
    Uses Ollama to categorize expenses.
    """
    messages = [
        {
            'role': 'user',
            'content': f"Categorize the following expense description: '{description}' for a trip to {location}, for an amount of {amount}. Possible categories are: Accommodation, Transport, Meals, Tours, Groceries, Airfare, Subscriptions, Recurring Payments, Other. Pay special attention to the description, if you find full or partial names of airline companies and expenses are on the higher side (say double digits to hundreds of dollars), then it is likely Airfare. Print only the category and nothing else.",
        },
    ]
    response = chat('gemma3:12b', messages=messages)
    category = response['message']['content'].strip()
    return category

def get_column_name(columnList, requiredColumnDescription):
    """
    Given a list of column names and a required column description,
    returns the best matching column name.
    """

    concatenatedColumnList = ",".join(columnList)

    messages = [
        {
            'role': 'user',
            'content': f"Among these columns in a credit card/banking statement, which one refers to the one with the '{requiredColumnDescription}'? {concatenatedColumnList}. Just list the name of the column.",
        },
    ]

    response = chat('gemma3:12b', messages=messages)
    category = response['message']['content'].strip()
    return category

# Example invocation
if __name__ == "__main__":
    start_date = "2025-12-16"
    end_date = "2025-12-23"
    location = "Cozumel, Mexico"
    accommodation = "Resort and Hotel"
    csv_files = ["financial_statement1.csv", "financial_statement2.csv"]

    categorized_expenses, total_expenditure = analyze_trip_expenses(start_date, end_date, location, accommodation, csv_files)

    print("Categorized Expenses:")
    print(categorized_expenses)
    print("\nTotal Expenditure:", total_expenditure)