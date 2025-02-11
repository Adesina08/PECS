import streamlit as st
import pandas as pd
from io import BytesIO

def process_data(df, selected_col):
    results = []
    
    for _, row in df.iterrows():
        state = row.get('state', '')
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
        
        # Corrected if statement
        if selected_col not in df.columns:
            st.error(f"Column '{selected_col}' not found in the uploaded file")
            st.stop()
            
        if 'State' not in df.columns or 'EAN' not in df.columns:
            st.error("File must contain both 'State' and 'EAN' columns")
            st.stop()
            
        result_df = process_data(df, selected_col)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Results')
            
            # Auto-adjust column widths
            workbook = writer.book
            worksheet = writer.sheets['Results']
            for i, col in enumerate(result_df.columns):
                max_len = max(result_df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_len)
        
        st.download_button(
            label="📥 Download Results",
            data=output.getvalue(),
            file_name="eligibility_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("Processing complete! Click the download button above for your results.")
        st.dataframe(result_df.head())
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
