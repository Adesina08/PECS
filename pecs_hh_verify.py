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
        
        eligible = []
        non_eligible = []
        
        for fig in figures:
            try:
                # Convert to integer and back to string to remove leading zeros
                num = str(int(fig))
                column_name = f'enfant_6_59_{num}'
                
                if column_name in df.columns:
                    value = str(row.get(column_name, '')).strip().lower()
                    if value in ['yes', '1']:
                        eligible.append(fig)  # Keep original formatting
                    else:
                        non_eligible.append(fig)
                else:
                    non_eligible.append(fig)
            except ValueError:
                non_eligible.append(fig)
        
        results.append({
            'state': state,
            'EAN': ean,
            'Total hh_selected count': total,
            'Eligible for main(has a child 6 -59 months)': ', '.join(eligible),
            'Total eligibility count': len(eligible),
            'Non eligible for main(has no child 6- 59 months)': ', '.join(non_eligible),
            'Total non eligibility count': len(non_eligible)
        })
    
    return pd.DataFrame(results)

st.title("Household Eligibility Analyzer")

uploaded_file = st.file_uploader("Upload data file", type=['xlsx', 'xls', 'csv'])
selected_col = st.text_input("Column name with household numbers", "selected_household")

if uploaded_file and selected_col:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        if selected_col not in df.columns:
            st.error(f"Column '{selected_col}' not found in the uploaded file")
            st.stop()
            
        if 'state' not in df.columns or 'EAN' not in df.columns:
            st.error("File must contain both 'state' and 'EAN' columns")
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
