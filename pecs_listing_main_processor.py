import streamlit as st
import pandas as pd
import os
import zipfile
from io import BytesIO
import uuid

def create_zip(folder_path):
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), 
                          os.path.relpath(os.path.join(root, file), folder_path))
    memory_file.seek(0)
    return memory_file

def main():
    st.title("EAN Data Processor 📁")
    
    # File Upload Section
    with st.expander("📤 Upload Files", expanded=True):
        ref_file = st.file_uploader("Upload Reference File (Excel)", type=['xlsx'])
        data_file = st.file_uploader("Upload Data File (Excel)", type=['xlsx'])

    # Column Configuration
    with st.expander("⚙️ Configure Columns", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Reference File")
            ref_ean_col = st.text_input("EAN Column Name (Reference)", "EAN")
            ref_secondary_col = st.text_input("Secondary Column Name (Reference)", "SecondaryCol")
            state_col = st.text_input("State Column Name", "State")
            
        with col2:
            st.subheader("Data File")
            data_ean_col = st.text_input("EAN Column Name (Data)", "EAN")
            data_secondary_col = st.text_input("Secondary Column Name (Data)", "SecondaryCol")

    if st.button("🚀 Process Files"):
        if not all([ref_file, data_file]):
            st.error("Please upload both files!")
            return

        try:
            # Read files
            ref_df = pd.read_excel(ref_file)
            data_df = pd.read_excel(data_file)

            # Validate columns
            required_ref_cols = [ref_ean_col, ref_secondary_col, state_col]
            required_data_cols = [data_ean_col, data_secondary_col]
            
            if not all(col in ref_df.columns for col in required_ref_cols):
                st.error("Missing columns in Reference File!")
                return
                
            if not all(col in data_df.columns for col in required_data_cols):
                st.error("Missing columns in Data File!")
                return

            # Merge data
            merged = ref_df.merge(
                data_df,
                left_on=[ref_ean_col, ref_secondary_col],
                right_on=[data_ean_col, data_secondary_col],
                how='left',
                indicator=True
            )

            # Check for missing EANs
            missing_eans = merged[merged['_merge'] == 'left_only'][ref_ean_col].unique()
            if len(missing_eans) > 0:
                st.warning(f"Missing {len(missing_eans)} EANs in Data File!")
                st.write("Missing EANs:", missing_eans)

            # Create folder structure
            base_path = f"temp_{uuid.uuid4()}"
            os.makedirs(base_path, exist_ok=True)

            # Group by state and EAN
            grouped = merged.groupby([state_col, ref_ean_col])
            
            for (state, ean), group in grouped:
                # Create state folder
                state_folder = os.path.join(base_path, str(state))
                os.makedirs(state_folder, exist_ok=True)
                
                # Create CSV file
                filename = os.path.join(state_folder, f"{ean}.csv")
                group.to_csv(filename, index=False)

            # Create ZIP
            zip_buffer = create_zip(base_path)
            
            # Download button
            st.success("Processing Complete!")
            st.download_button(
                label="📥 Download Results",
                data=zip_buffer,
                file_name="processed_data.zip",
                mime="application/zip"
            )

        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
            
if __name__ == "__main__":
    main()
