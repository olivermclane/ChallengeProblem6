# CSV Splitter and Statistical Analysis Tool

Author: Oliver McLane
Date: 2024-04-24

This Python script allows you to split CSV data into multiple different CSV files named Teams.csv and Institutions.csv. It utilizes a fuzzy-match based algorithm to group together similar university names. The tool also conducts a series of statistical analyses and outputs the results into separate CSV files.
##  Features

- Fuzzy Grouping: Dynamically groups institution names based on similarity to handle minor spelling variations. In this you can adjust the hyperparameter for the fuzzy match, currently it's set at `87` this can be tuned at user discretion 
- Data Validation: Checks for necessary columns and handles missing data effectively.

##  Prerequisites

Before running this script, ensure you have the following installed:

- Python 3.x 

### Clone Repo
```bash
git clone https://github.com/olivermclane/ChallengeProblem5
```

Next, you can install the required Python libraries using pip:

```bash
pip install -r requirements.txt
```
- pandas library (Csv manipulator library)
- fuzzywuzzy library (Used to fuzzy match strings to prevent duplicates in the database)


To use this script, your input CSV file must contain the following headers:
- Institution
- City
- State/Province
- Country
- Team Number
- Advisor
- Problem
- Ranking

## Running the Script
Navigate to the script's directory and run the following command:

```bash 
python main.py
```
The script will prompt you to enter the location of your CSV file. You can input a direct path to your file or use `1` for a test file named 2015.csv, or `2` to exit.

## Output Files
After processing, the script generates two CSV files:

- Institutions.csv: Contains unique institutions with IDs.
- Teams.csv: Contains team details linked to their respective institutions.

Navigate to results and view results:
```bash
cd results
```
