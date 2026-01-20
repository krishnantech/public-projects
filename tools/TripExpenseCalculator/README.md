
# Trip Expense Calculator

This is a tool to help categorize and calculate totals of all expenses undertaken on a trip, including various categories like flights/transport, accommodations, tours, meals, grocery purchases, etc. Inputs include a date range for the trip and bank/credit card statements for relevant duration of trip expenses. The tool uses Local AI to prevent confidential data leakage.

## Status

Prototype

## Usage

```bash
python TripExpenseCalculator.py --start-date <yyyy-mm-dd> --end-date <yyyy-mm-dd> --location <location> --files "path-to-statement1.csv","path-to-statement2.csv",... --output-file <desired name of output excel file>
