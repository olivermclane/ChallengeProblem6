"""
Author: Oliver McLane
Date: 2024-04-24
This file allows you to split csv data into multiple different csv called Team.csv and Institutions.csv, it uses a fuzzy-match
based algorithm that matches together different universities together. You are prompted to either enter a csv path, test with the
preset file or quit the CLI tool. It will also conduct a series of statistical analysis and spit them out into several csv.
"""
import pandas as pd
from fuzzywuzzy import process, fuzz

# Define a dictionary to convert US state abbreviations to full names
state_abbreviations = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"
}

"""
    @ param threshold    Adjusting the threshold will adjust how much of a match the institutions name needs to be to 
                        get grouped. The higher the number the more similar the names need to be and vice versa.
"""


def fuzzy_grouping(dataframe, column_name, threshold=89):
    # Extract unique institution names
    names = dataframe[column_name].unique()
    # Dictionary to hold the mapping from original to grouped name
    grouped_names = {}

    # Iterate through each name
    for name in names:
        if grouped_names:
            # Check for fuzzy match in already grouped names
            match, score = process.extractOne(name, list(grouped_names.keys()), scorer=fuzz.token_sort_ratio)
            if score > threshold:
                # If a close match is found above threshold, group it under the matched name
                grouped_names[name] = grouped_names[match]
            else:
                # Otherwise, group it under itself
                grouped_names[name] = name
        else:
            # Initialize with the first name if empty
            grouped_names[name] = name

    # Apply the grouping to the original dataframe column
    dataframe['Grouped Institution'] = dataframe[column_name].map(grouped_names)
    return dataframe


"""
Data wrangling function, used to clean and group the fields for csv and statistical analysis.
"""


def save_csv(file_path):
    # Try to load the data from the CSV file
    try:
        # Load the data from the CSV file
        data_2015 = pd.read_csv(file_path)
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    # Check for the required headers in the CSV
    required_columns = {'Institution', 'City', 'State/Province', 'Country', 'Team Number', 'Advisor', 'Problem',
                        'Ranking'}
    if not required_columns.issubset(data_2015.columns):
        missing_columns = required_columns - set(data_2015.columns)
        print(f"Missing required columns: {missing_columns}")
        return

    # Apply fuzzy grouping to the institution names
    data_2015 = fuzzy_grouping(data_2015, 'Institution')

    # Replace nulls in 'State/Province' with 'Unknown'
    data_2015.loc[:, 'State/Province'] = data_2015['State/Province'].fillna('Unknown')

    for column in data_2015.columns:
        if data_2015[column].dtype == object and column != 'Country':
            if column == 'State/Province':
                # Convert 2-letter abbreviations to full names
                data_2015[column] = data_2015[column].str.strip().apply(
                    lambda x: state_abbreviations[x.upper()] if x.upper() in state_abbreviations and len(x) == 2 else x)
            elif column != 'Advisor':  # Skip capitalization for 'Advisor'
                # Capitalize other columns
                data_2015[column] = data_2015[column].str.strip().str.capitalize()

    # Creating a unique list of institutions
    institutions = data_2015[['Grouped Institution', 'City', 'State/Province', 'Country']].drop_duplicates(
        subset=['Grouped Institution'])

    institutions.reset_index(drop=True, inplace=True)
    institutions.index.name = 'Institution ID'
    institutions.reset_index(inplace=True)
    institutions.columns = ['Institution ID', 'Institution Name', 'City', 'State/Province', 'Country']

    # Save the Institutions CSV file
    institutions_path = 'results/Institutions.csv'
    institutions.to_csv(institutions_path, index=False)

    # Merging team data with grouped institutions to get the correct Institution ID
    team_details_correct = data_2015[['Team Number', 'Advisor', 'Problem', 'Ranking', 'Grouped Institution']].copy()
    team_details_correct = team_details_correct.merge(institutions[['Institution Name', 'Institution ID']],
                                                      left_on='Grouped Institution', right_on='Institution Name',
                                                      how='left')
    team_details_correct.drop('Institution Name', axis=1, inplace=True)

    # Save the Teams CSV file
    teams_path = 'results/Teams.csv'
    team_details_correct.to_csv(teams_path, index=False)

    print("SQL ready files saved:", institutions_path, teams_path)

    # Return the data frames for statistical analysis
    return team_details_correct, institutions


def get_statistical_analysis_file(teams_df, institutions_df):
    # Convert 'Institution ID' to integer
    teams_df['Institution ID'] = teams_df['Institution ID'].astype(int)

    # Calculate the average number of teams per institution
    avg_teams_per_institution = int(teams_df.groupby('Institution ID')['Team Number'].nunique().mean())
    print("Average Teams per Institution: ", avg_teams_per_institution)

    # Count the number of teams per institution
    institutions_teams_count = teams_df['Institution ID'].value_counts().reset_index()
    institutions_teams_count.columns = ['Institution ID', 'Number of Teams']

    # Merge with institutions_df to get institution details
    top_institutions = institutions_teams_count.merge(institutions_df, on='Institution ID').sort_values(
        by='Number of Teams', ascending=False)

    # Filter institutions that received 'Outstanding' rankings
    outstanding_institutions = teams_df[teams_df['Ranking'] == 'Outstanding winner']['Institution ID'].unique()
    outstanding_institutions_list = institutions_df[
        institutions_df['Institution ID'].isin(outstanding_institutions)].sort_values(by='Institution Name')

    # Merge with institutions_df to get country information
    team_df_with_country = teams_df.merge(institutions_df[['Institution ID', 'Country']], on='Institution ID',
                                          how='left')

    # Filter US teams with 'Meritorious' ranking or better
    us_teams_meritorious_or_better = team_df_with_country[(team_df_with_country['Country'] == 'USA') & (
        team_df_with_country['Ranking'].isin(['Outstanding winner', 'Meritorious']))]

    # Output paths
    outstanding_institutions_list_path = 'results/Outstanding_Institutions.csv'
    outstanding_institutions_list.to_csv(outstanding_institutions_list_path, index=False)
    print("Path to Outstanding Institutions:", outstanding_institutions_list_path)

    top_institutions_path = 'results/Top_Institutions.csv'
    top_institutions.to_csv(top_institutions_path, index=False)
    print("Path to Top Institutions:", top_institutions_path)

    us_teams_meritorious_or_better_path = 'results/US_Teams_Meritorious_or_Better.csv'
    us_teams_meritorious_or_better.to_csv(us_teams_meritorious_or_better_path, index=False)
    print("Path to US Teams with Meritorious or Better Ranking:", us_teams_meritorious_or_better_path)


def main():
    end_flag = False
    while not end_flag:
        file_location = input(
            "CSV splitting and computing statistical analysis CLI tool. Type a location of file or, (1) for the test "
            "file (2015.csv), or (2) for exit: ")
        if file_location == "1":
            file_path = 'data/2015.csv'
            teams_df, institutions_df = save_csv(file_path)
            get_statistical_analysis_file(teams_df, institutions_df)
            end_flag = True
        elif file_location == "2":
            print("Quitting...")
            end_flag = True
        else:
            file_path = file_location
            teams_df, institutions_df = save_csv(file_path)
            get_statistical_analysis_file(teams_df, institutions_df)


if __name__ == '__main__':
    main()
