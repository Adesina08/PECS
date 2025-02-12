import streamlit as st
import pandas as pd
import re
from io import BytesIO

def process_data(df):
    results = []
    # Find all columns matching the enfant_6_59_# pattern
    enfant_cols = [col for col in df.columns if re.fullmatch(r'enfant_6_59_\d+', col)]
    
    for _, row in df.iterrows():
        state = row.get('state', '')
        ean = row.get('EAN', '')
        
        eligible = []
        non_eligible = []
        
        for col in enfant_cols:
            value = row[col]
            # Check if value is not blank/empty
            if pd.notna(value) and str(value).strip() != '':
                # Extract household number from column name
                household_number = col.split('_')[-1]
                # Check eligibility
                cleaned_value = str(value).strip().lower()
                if cleaned_value in ['yes', '1']:
                    eligible.append(household_number)
                else:
                    non_eligible.append(household_number)
        
        total_hh_listed = len(eligible) + len(non_eligible)
        
        results.append({
            'state': state,
            'EAN': ean,
            'total hh_listed': total_hh_listed,
            'Eligible for main(has a child 6 -59 months)': ', '.join(eligible),
            'Total eligibility count': len(eligible),
            'Non eligible for main(has no child 6- 59 months)': ', '.join(non_eligible),
            'Total non eligibility count': len(non_eligible)
        })
    
    return pd.DataFrame(results)

st.title("Auto Household Eligibility Analyzer")

uploaded_file = st.file_uploader("Upload data file", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    try:
        # Read the uploaded file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Validate required columns
        if 'state' not in df.columns or 'EAN' not in df.columns:
            st.error("File must contain both 'state' and 'EAN' columns")
            st.stop()
            
        # Check for existence of enfant columns
        enfant_cols = [col for col in df.columns if re.fullmatch(r'enfant_6_59_\d+', col)]
        if not enfant_cols:
            st.error("No columns matching pattern 'enfant_6_59_#' found in the file")
            st.stop()
            
        # Process data
        result_df = process_data(df)
        
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
        
        # Download button
        st.download_button(
            label="📥 Download Results",
            data=output.getvalue(),
            file_name="auto_eligibility_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("Processing complete! Click the download button above for your results.")
        st.dataframe(result_df.head())
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
