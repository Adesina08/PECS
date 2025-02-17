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
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    memory_file.seek(0)
    return memory_file

def read_file(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        return pd.read_excel(file, engine='openpyxl')
    else:
        raise ValueError("Unsupported file format")

def main():
    st.title("📁 Advanced EAN Processor")
    
    # Initialize session state
    if 'ref_df' not in st.session_state:
        st.session_state.ref_df = None
    if 'data_df' not in st.session_state:
        st.session_state.data_df = None

    # File upload section
    with st.expander("📤 STEP 1: Upload Files", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            ref_file = st.file_uploader("Reference File", type=['xlsx', 'csv'])
            if ref_file:
                st.session_state.ref_df = read_file(ref_file)
        with col2:
            data_file = st.file_uploader("Data File", type=['xlsx', 'csv'])
            if data_file:
                st.session_state.data_df = read_file(data_file)

    # Column configuration
    with st.expander("⚙️ STEP 2: Configure Columns", expanded=True):
        col1, col2 = st.columns(2)
        selected_cols = {}
        
        with col1:
            st.subheader("Reference File")
            if st.session_state.ref_df is not None:
                ref_cols = st.session_state.ref_df.columns.tolist()
                selected_cols['ref_ean'] = st.selectbox("EAN Column", ref_cols, key='ref_ean')
                selected_cols['ref_secondary'] = st.selectbox("Secondary Column", ref_cols, key='ref_secondary')
                selected_cols['state'] = st.selectbox("State Column", ref_cols, key='state')
            else:
                st.info("Upload reference file to configure columns")

        with col2:
            st.subheader("Data File")
            if st.session_state.data_df is not None:
                data_cols = st.session_state.data_df.columns.tolist()
                selected_cols['data_ean'] = st.selectbox("EAN Column", data_cols, key='data_ean')
                selected_cols['data_secondary'] = st.selectbox("Secondary Column", data_cols, key='data_secondary')
            else:
                st.info("Upload data file to configure columns")

    if st.button("🚀 PROCESS FILES", type="primary"):
        if not all([st.session_state.ref_df is not None, st.session_state.data_df is not None]):
            st.error("Please upload both files before processing")
            return

        try:
            ref_df = st.session_state.ref_df.copy()
            data_df = st.session_state.data_df.copy()

            # Merge datasets
            merged = ref_df.merge(
                data_df,
                left_on=[selected_cols['ref_ean'], selected_cols['ref_secondary']],
                right_on=[selected_cols['data_ean'], selected_cols['data_secondary']],
                how='left',
                indicator=True
            )

            # Handle missing EANs
            missing_mask = merged['_merge'] == 'left_only'
            missing_eans = merged[missing_mask][selected_cols['ref_ean']].unique()
            
            # Create output structure
            base_path = f"output_{uuid.uuid4()}"
            os.makedirs(base_path, exist_ok=True)

            # Create missing EANs report
            if len(missing_eans) > 0:
                missing_df = pd.DataFrame({
                    'Missing EANs': missing_eans,
                    'state': merged[missing_mask][selected_cols['state']].unique()[0]
                })
                missing_path = os.path.join(base_path, "missing_eans.xlsx")
                missing_df.to_excel(missing_path, index=False)

            # Create state folders and EAN files
            grouped = merged.groupby([selected_cols['state'], selected_cols['ref_ean']])
            for (state, ean), group in grouped:
                state_folder = os.path.join(base_path, str(state))
                os.makedirs(state_folder, exist_ok=True)
                
                output_path = os.path.join(state_folder, f"{ean}.csv")
                group.drop(columns='_merge').to_csv(output_path, index=False)

            # Create ZIP download
            zip_buffer = create_zip(base_path)
            
            # Download button
            st.success("✅ Processing complete!")
            st.download_button(
                label="📥 DOWNLOAD RESULTS",
                data=zip_buffer,
                file_name="processed_data.zip",
                mime="application/zip",
                help="Contains organized CSV files and missing EANs report"
            )

        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")

if __name__ == "__main__":
    main()
