#!/usr/bin/env python
"""
process_rosters.py

Given a directory of rosters, create a single dataframe, create
additions for masterlist, and create college reports.
"""
import json
import os
import shutil

import pandas as pd


def get_config():
    with open('../config.json', 'r') as f:
        config = json.load(f)
        print('Configuration loaded {}'.format(config))

        return config


def get_roster():
    rosters = [pd.read_excel(os.path.join('../data', x),)
               for x in os.listdir('../data')]
    combined_roster = pd.concat(rosters, ignore_index=True)
    participants = combined_roster['First Name'].count()
    print(
        '{} participants found. Please manually check this '
        'against the excel sheet in order to test for data '
        'loss.'.format(participants))

    return combined_roster


def clean_roster(roster):
    # Normalize name/email data
    roster['First Name'] = roster['First Name'].str.title()
    roster['Last Name'] = roster['Last Name'].str.title()
    roster['Academic Supervisor'] = roster['Academic Supervisor'].str.title()
    roster['Supervisor Email'] = roster['Supervisor Email'].str.lower()
    roster['Alternate Email Address'] = roster[
        'Alternate Email Address'].str.lower()
    roster['CUNY Email'] = roster['CUNY Email'].str.lower()
    roster['College or School'] = roster['College or School'].str.upper()
    roster['Discipline'] = roster['Discipline'].str.title()
    roster['Full Name'] = roster.apply(lambda x: create_full_name(x), axis=1)

    # Convert status to categorial
    roster['Final Status'] = roster['Final Status'].str.title()
    roster['Final Status'] = roster['Final Status'].astype('category')
    roster['College or School'] = roster['College or School'].astype(
        'category')

    # Drop cols
    cols_to_drop = [
        'Comments', 'Course Number and Title', 'Faculty Status',
        'Familiarity With Blackboard', 'Final Points']

    roster = roster.drop(cols_to_drop, axis=1)
    roster.to_json('../output/pto_data_{}.json'.format(config['end_date']))

    return roster


def create_full_name(row):
    return '{}, {}'.format(row['Last Name'], row['First Name'])


def create_particiption_data(roster):
    pto = roster[['Full Name', 'Final Status', 'College or School',
                  'Academic Supervisor']]
    # participant_count = len(pto['Final Status'])
    pass_count = len(pto[pto['Final Status'] == 'Pass'])
    no_pass_count = len(pto[pto['Final Status'] == 'No Pass'])
    withdraw_count = len(pto[pto['Final Status'] == 'Withdraw'])
    college_school_count = len(pto['College or School'].cat.categories)
    print('Participants from {} units of CUNY.\n{} passed,'
          ' {} did not pass, and {} withdrew.'.format(
              college_school_count,
              pass_count,
              no_pass_count,
              withdraw_count))
    order = ['Full Name', 'College or School', 'Final Status',
             'Academic Supervisor']
    pto.to_json('../output/participation_data_'
                '{}.json'.format(config['end_date']),
                columns=order)


def create_addition_data(roster):
    roster = roster.drop(['Academic Supervisor', 'Alternate Email Address',
                          'First Name', 'Last Name', 'Supervisor Email'],
                         axis='columns')
    # Map column names so appending is easier
    mapping = {'CUNY Email': 'Email Address',
               'College or School': 'College/School',
               'Discipline': 'Concentration / Program',
               'Unnamed: 14': 'Comment', 'Full Name': 'Name',
               'Final Status': 'Status'}
    roster = roster.rename(columns=mapping)
    # Fill ins
    roster['Date'] = config['end_date']
    roster['Semester'] = config['term']
    roster['Secondary C / P'] = ' '
    order = ['Name', 'Date', 'Semester', 'Status', 'Concentration / Program',
             'Secondary C / P', 'College/School', 'Email Address', 'Comment']
    roster.to_json('../output/reports/masterlist_addition_{}.json'
                   .format(config['end_date']), columns=order)

if __name__ == '__main__':
    config = get_config()
    x = get_roster()
    x = clean_roster(x)
    create_particiption_data(x)
    create_addition_data(x)
