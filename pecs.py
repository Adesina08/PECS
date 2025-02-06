import streamlit as st
import pandas as pd
import os
import re
import zipfile
import io

def create_zip_file(directory):
    """Create a ZIP file containing all files from the directory structure"""
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory)
                zipf.write(file_path, arcname)
    memory_file.seek(0)
    return memory_file

def process_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    
    # Check required columns
    required_columns = ['state', 'EAN']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("CSV must contain 'state' and 'EAN' columns")
    
    # Extract and sort longitude columns (updated regex pattern)
    long_columns = []
    for col in df.columns:
        match = re.match(r'location_gps-Longitude_(\d+)', col)
        if match:
            suffix = int(match.group(1))
            long_columns.append((suffix, col))
    
    if not long_columns:
        raise ValueError("CSV must contain longitude columns (location_gps-Longitude_1, location_gps-Longitude_2, etc.)")
    
    long_columns.sort(key=lambda x: x[0])
    
    base_dir = "processed_data"
    os.makedirs(base_dir, exist_ok=True)
    
    for index, row in df.iterrows():
        state = row['state']
        EAN = row['EAN']
        
        # Create state directory
        state_dir = os.path.join(base_dir, state)
        os.makedirs(state_dir, exist_ok=True)
        
        # Process coordinates
        listings = []
        for suffix, long_col in long_columns:
            long_val = row[long_col]
            if pd.isnull(long_val):
                break
            
            # Updated latitude column name
            lat_col = f'location_gps-Latitude_{suffix}'
            lat_val = row.get(lat_col, None)
            
            listings.append({
                'state': state,
                'EAN': EAN,
                'listing_count': f"{EAN}_{suffix}",
                'long': long_val,
                'lat': lat_val if not pd.isnull(lat_val) else None
            })
        
        if listings:
            # Create EAN DataFrame
            EAN_df = pd.DataFrame(listings)
            
            # Save to CSV
            filename = f"{EAN}.csv"
            filepath = os.path.join(state_dir, filename)
            EAN_df.to_csv(filepath, index=False)
    
    return base_dir

def main():
    st.title("PECS LISITNG EA SPLITTER")
    
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            base_dir = process_csv(uploaded_file)
            st.success("Processing completed successfully!")
            
            # Create download button for the zip file
            zip_file = create_zip_file(base_dir)
            st.download_button(
                label="Download Splitted EAs",
                data=zip_file,
                file_name="Splitted EAs.zip",
                mime="application/zip"
            )
            
            st.balloons()
            
            # ClEAN up the processed_data directory
            import shutil
            shutil.rmtree(base_dir)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
