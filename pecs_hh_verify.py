import streamlit as st
import pandas as pd
from io import BytesIO

def process_data(df, selected_col):
    results = []
    
    for _, row in df.iterrows():
        state = row.get('State', '')
        ean = row.get('EAN', '')
        household_numbers = str(row.get(selected_col, '')).strip()
        
        # Split and clean household numbers
        figures = [f.strip() for f in household_numbers.split(',') if f.strip()]
        total = len(figures)
        
        eligible = 0
        non_eligible = 0
        
        for fig in figures:
            column_name = f'enfant_6_59_{fig}'
            if column_name in df.columns:
                if pd.notna(row[column_name]) and row[column_name].strip().lower() == 'yes':
                    eligible += 1
                else:
                    non_eligible += 1
            else:
                non_eligible += 1
        
        results.append({
            'State': state,
            'EAN': ean,
            'Total hh_selected count': total,
            'Eligible for main(has a child 6 -59 months)': eligible,
            'Non eligible for main(has no child 6- 59 months)': non_eligible
        })
    
    return pd.DataFrame(results)

st.title("Household Eligibility Analyzer")

uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])
selected_col = st.text_input("Column name with household numbers", "selected_household")

if uploaded_file and selected_col:
    try:
        df = pd.read_excel(uploaded_file)
        
        if selected_col not in df.columns
