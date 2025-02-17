import streamlit as st
import pandas as pd
import os
import zipfile
from io import BytesIO
import uuid

def create_zip(folder_path):
    """Create in-memory ZIP archive from folder structure"""
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    memory_file.seek(0)
    return memory_file

def read_file(file):
    """Read uploaded file with format validation"""
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        return pd.read_excel(file, engine='openpyxl')
    else:
        raise ValueError("Unsupported file format")

def validate_columns(df, required_cols, file_name):
    """Validate presence of required columns in dataframe"""
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {file_name}: {', '.join(missing)}")

def main():
    st.title("📁 EAN Data Processor")
    st.markdown("### Upload your reference and data files")

    # File upload section
    with st.expander("📤 STEP 1: Upload Files", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            ref_file = st.file_uploader("Reference File", type=['xlsx', 'csv'])
        with col2:
            data_file = st.file_uploader("Data File", type=['xlsx', 'csv'])

    # Column configuration
    with st.expander("⚙️ STEP 2: Configure Columns", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Reference File Columns")
            ref_ean_col = st.text_input("EAN Column Name", "EAN", key="ref_ean")
            ref_secondary_col = st.text_input("Secondary Column Name", "SecondaryCol", key="ref_sec")
            state_col = st.text_input("State Column Name", "State", key="state")
            
        with col2:
            st.subheader("Data File Columns")
            data_ean_col = st.text_input("EAN Column Name", "EAN", key="data_ean")
            data_secondary_col = st.text_input("Secondary Column Name", "SecondaryCol", key="data_sec")

    # Processing button
    if st.button("🚀 PROCESS FILES", type="primary"):
        if not all([ref_file, data_file]):
            st.error("Please upload both files before processing")
            return

        try:
            # Validate file formats
            if any(f.name.endswith(('.xlsm', '.xls')) for f in [ref_file, data_file]):
                raise ValueError("Macro-enabled or legacy Excel files are not supported")

            # Read and validate files
            ref_df = read_file(ref_file)
            data_df = read_file(data_file)

            # Validate columns
            validate_columns(ref_df, [ref_ean_col, ref_secondary_col, state_col], "Reference File")
            validate_columns(data_df, [data_ean_col, data_secondary_col], "Data File")

            # Merge datasets
            merged = ref_df.merge(
                data_df,
                left_on=[ref_ean_col, ref_secondary_col],
                right_on=[data_ean_col, data_secondary_col],
                how='left',
                indicator=True
            )

            # Handle missing EANs
            missing_mask = merged['_merge'] == 'left_only'
            if missing_mask.any():
                missing_eans = merged.loc[missing_mask, ref_ean_col].unique()
                st.warning(f"⚠️ Missing {len(missing_eans)} EANs in Data File")
                st.write("Missing EAN numbers:", ", ".join(map(str, missing_eans)))

            # Create folder structure
            base_path = f"output_{uuid.uuid4()}"
            os.makedirs(base_path, exist_ok=True)

            # Group and save results
            for (state, ean), group in merged.groupby([state_col, ref_ean_col]):
                state_folder = os.path.join(base_path, str(state))
                os.makedirs(state_folder, exist_ok=True)
                
                output_path = os.path.join(state_folder, f"{ean}.csv")
                group.drop(columns='_merge').to_csv(output_path, index=False)

            # Create ZIP download
            zip_buffer = create_zip(base_path)
            
            # Display success and download button
            st.success("✅ Processing complete!")
            st.download_button(
                label="📥 DOWNLOAD RESULTS",
                data=zip_buffer,
                file_name="processed_data.zip",
                mime="application/zip",
                help="Contains organized CSV files in state folders"
            )

        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")

if __name__ == "__main__":
    main()
