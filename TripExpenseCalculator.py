from ollama import chat
import pandas as pd
from datetime import datetime, timedelta
import dateutil.parser as date_parser
from LocalAIService import LocalAIService
from Logger import ConsoleLogger
from ExcelOutputWriter import ExcelOutputWriter

# Create a default AI service instance
_ai_service = LocalAIService("gemma3:12b")
_logger = ConsoleLogger()

def analyze_trip_expenses(start_date, end_date, location, csv_files, output_file_name):
    """
    Analyzes trip expenses from financial statements using a local AI model.

    Args:
        start_date (str): Start date of the trip (YYYY-MM-DD).
        end_date (str): End date of the trip (YYYY-MM-DD).
        location (str): Location of the trip.
        csv_files (list): List of paths to CSV files containing financial statements.

    Returns:
        dict: A dictionary containing categorized expenses and total trip expenditure.
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    advance_booking_months = 3  # Check for advance bookings up to 1 month prior

    all_expenses = []

    for csv_file in csv_files:
        _logger.log_info(f"Processing file: {csv_file}")
        _logger.log_info("-" * 20)
        _logger.log_info("")

        df = pd.read_csv(csv_file)

        columnListFromCsv = df.columns.tolist()
        
        # Identify relevant date, description and amount columns
        date_column = _ai_service.get_column_name(columnListFromCsv, "transaction date")
        description_column = _ai_service.get_column_name(columnListFromCsv, "name of the merchant")
        amount_column = _ai_service.get_column_name(columnListFromCsv, "transaction amount")

        _logger.log_info(f"Relevant columns from CSV detected. Using columns {date_column} for Date, {description_column} for Description, {amount_column} for Amount")

        df['date'] = pd.to_datetime(df[date_column])

        for index, row in df.iterrows():
            transaction_date = row[date_column]
            description = row[description_column]
            amount = row[amount_column] 
            transaction_date_parsed = date_parser.parse(transaction_date) 
            category = "Other"

            # Filter transactions within the trip dates or for advance bookings
            if transaction_date_parsed >= start_date and transaction_date_parsed <= end_date:
                category = _ai_service.categorize_expense(description, amount)

            elif transaction_date_parsed >= (start_date - timedelta(days=advance_booking_months * 30)) and transaction_date_parsed <= (start_date - timedelta(days=1)):
                # Categorize expenses for advance bookings. We will look for specific types here (airfare, accommodation)
                category = _ai_service.categorize_expense(description, amount)
                if(category not in ("Airfare", "Accommodation")):
                    _logger.log_transaction(transaction_date_parsed, description, amount, category, status="Ignored", sub_status="Older irrelevant transaction")
                    continue  

            elif transaction_date_parsed == (end_date + timedelta(days=1)):
                # Include transactions made the day after the trip ends (e.g., hotel check-out charges)
                category = _ai_service.categorize_expense(description, amount)
                if(category not in ("Accommodation", "Other", "Transport")):
                    continue

            else:
                # Ignore transactions outside the trip date range and advance booking window
                continue
    
            # ignore subscriptions, recurring/credit card payments
            if (category not in ["Subscriptions", "Recurring Payments", "Credit Card Payments", "Other Credits"]):
                _logger.log_transaction(transaction_date_parsed, description, amount, category, status="Accepted")
                all_expenses.append({'date': transaction_date, 'description': description, 'amount': abs(amount), 'category': category})
            else:
                _logger.log_transaction(transaction_date_parsed, description, amount, category, status="Ignored", sub_status="Subscription/Recurring Payment")

        _logger.log_info("")

    # Print all expenses by category
    _logger.print_expenses_by_category(all_expenses)

    # Group expenses by category and calculate sums
    categorized_expenses, total_expenditure = _logger.calculate_and_print_total_expenses_by_category(all_expenses)

    output_writer = ExcelOutputWriter(f"{output_file_name}.xlsx")
    output_writer.write_expenses(all_expenses, categorized_expenses, total_expenditure)

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze trip expenses from financial statements using AI categorization.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python TripExpenseCalculator.py -s 2024-12-01 -e 2024-12-10 -l California -f statement1.csv,statement2.csv -o CaliforniaTrip2024
  python TripExpenseCalculator.py --start-date 2024-12-01 --end-date 2024-12-10 --location California --files statement1.csv,statement2.csv --output-file CaliforniaTrip2024
        """
    )
    
    parser.add_argument(
        '-s', '--start-date',
        required=True,
        help='Start date of the trip (YYYY-MM-DD)'
    )
    parser.add_argument(
        '-e', '--end-date',
        required=True,
        help='End date of the trip (YYYY-MM-DD)'
    )
    parser.add_argument(
        '-l', '--location',
        required=True,
        help='Location of the trip'
    )
    parser.add_argument(
        '-f', '--files',
        type=str,
        required=True,
        help='Paths to CSV files containing financial statements (comma-separated)'
    )
    parser.add_argument(
        '-o', '--output-file',
        required=True,
        help='Output file name (without .xlsx extension)'
    )
    
    args = parser.parse_args()
    
    csv_files = [f.strip() for f in args.files.split(',')]
    analyze_trip_expenses(
        args.start_date,
        args.end_date,
        args.location,
        csv_files,
        args.output_file
    )