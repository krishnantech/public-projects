
# Trip Expense Calculator

This is a tool to help categorize and calculate totals of all expenses undertaken on a trip, including various categories like flights/transport, accommodations, tours, meals, grocery purchases, etc. Inputs include a date range for the trip and bank/credit card statements for relevant duration of trip expenses. The tool uses Local AI to prevent confidential data leakage.

## Status

Prototype

## Prerequisites
The tool requires:
1) [Ollama](https://ollama.com/), a service that allows running inferencing on various public models (e.g. gpt-oss, DeepSeek-R1, Gemma 3 and other models) locally.
2) Gemma-3:12b model installed on top of Ollama. Other model choices may be utilized too, with minor changes to the tool. 

## Usage

```bash
python TripExpenseCalculator.py --start-date <yyyy-mm-dd> --end-date <yyyy-mm-dd> --location <location> --files "path-to-statement1.csv","path-to-statement2.csv",... --output-file <desired name of output excel file>
