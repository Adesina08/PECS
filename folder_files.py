import streamlit as st
import zipfile
import os
import pandas as pd
from io import BytesIO
import tempfile

def main():
    st.title("ZIP Image Extractor")
    
    # File uploader for ZIP file
    uploaded_file = st.file_uploader("Upload a ZIP file", type="zip")
    
    if uploaded_file is not None:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                # Read the zip file
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    # Extract all files to temporary directory
                    zip_ref.extractall(tmp_dir)
                    
                    # Get all image files
                    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
                    image_files = []
                    
                    # Walk through the extracted directory
                    for root, dirs, files in os.walk(tmp_dir):
                        for file in files:
                            if os.path.splitext(file)[1].lower() in image_extensions:
                                image_files.append(file)
                    
                    # Create DataFrame with filenames
                    if image_files:
                        df = pd.DataFrame(image_files, columns=["Image Filenames"])
                        
                        # Create Excel file in memory
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Images')
                        
                        # Add download button
                        st.success(f"Found {len(image_files)} image files!")
                        st.download_button(
                            label="Download Excel File",
                            data=output.getvalue(),
                            file_name="image_filenames.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("No image files found in the ZIP archive")
                        
            except zipfile.BadZipFile:
                st.error("Invalid ZIP file. Please upload a valid ZIP archive.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
