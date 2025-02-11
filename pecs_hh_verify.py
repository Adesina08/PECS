import streamlit as st
import pandas as pd

# Function to process the data and generate the output DataFrame
def process_data(df, selected_column):
    # Initialize the result DataFrame
    result = pd.DataFrame(columns=["State", "EAN", "Total hh_selected count", 
                                   "Eligible for main (has a child 6-59 months)", 
                                   "Non eligible for main (has no child 6-59 months)"])
    
    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        state = row["state"]
        ean = row["EAN"]
        household_numbers = row[selected_column].split(",") if isinstance(row[selected_column], str) else []
        household_numbers = [num.strip().zfill(3) for num in household_numbers]
        
        total_count = len(household_numbers)
        eligible = []
        non_eligible = []
        
        for num in household_numbers:
            column_name = f"enfant_6_59_{num}"
            if column_name in df.columns:
                value = row[column_name]
                if value == "Yes":
                    eligible.append(num)
                else:
                    non_eligible.append(num)
        
        # Append the results to the result DataFrame
        result = result.append({
            "State": state,
            "EAN": ean,
            "Total hh_selected count": total_count,
            "Eligible for main (has a child 6-59 months)": ", ".join(eligible),
            "Non eligible for main (has no child 6-59 months)": ", ".join(non_eligible)
        }, ignore_index=True)
    
    return result

# Function to convert DataFrame to Excel file and provide a download link
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    output.seek(0)
    return output

# Streamlit App
st.title("Household Data Processor")

# File uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Read the uploaded Excel file
        df = pd.read_excel(uploaded_file)
        
        # Column selector
        selected_column = st.selectbox("Select the column containing household numbers:", df.columns)
        
        if selected_column:
            # Process the data
            result_df = process_data(df, selected_column)
            
            # Display the processed data
            st.write("Processed Data:")
            st.dataframe(result_df)
            
            # Download button
            excel_file = convert_df_to_excel(result_df)
            st.download_button(
                label="Download Processed Data as Excel",
                data=excel_file,
                file_name="processed_data.xlsx",
                mime="application/vnd.ms-excel"
            )
    except Exception as e:
        st.error(f"An error occurred: {e}")
