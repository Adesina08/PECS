import streamlit as st
import pandas as pd
import os
import re
import zipfile
import io
import shutil

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
    """
    Process the uploaded CSV file and create individual files for each EAN
    
    Args:
        uploaded_file: Streamlit uploaded file object
    
    Returns:
        str: Path to the base directory containing processed files
    
    Raises:
        ValueError: If required columns are missing or format is incorrect
    """
    df = pd.read_csv(uploaded_file)
    
    # Check required columns
    required_columns = ['state', 'EAN']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("CSV must contain 'state' and 'EAN' columns")
    
    # Convert EAN column to string and clean it
    df['EAN'] = df['EAN'].astype(str).str.strip()
    df['state'] = df['state'].astype(str).str.strip()
    
    # Remove rows with empty or null values in required columns
    df = df.dropna(subset=['state', 'EAN'])
    df = df[df['state'] != '']
    df = df[df['EAN'] != '']
    
    # Check for both possible column patterns
    long_columns = []
    using_generic_columns = False
    
    # First try numbered longitude columns
    for col in df.columns:
        match = re.match(r'location_gps-Longitude_(\d+)', col)
        if match:
            suffix = int(match.group(1))
            long_columns.append((suffix, col))
    
    # If no numbered columns found, check for generic columns
    if not long_columns:
        if 'Longitude' in df.columns and 'Latitude' in df.columns:
            long_columns = [(1, 'Longitude')]
            using_generic_columns = True
        else:
            raise ValueError(
                "CSV must contain either: \n"
                "- Numbered longitude columns (location_gps-Longitude_1, location_gps-Longitude_2, etc.)\n"
                "- OR generic 'Latitude' and 'Longitude' columns"
            )
    
    long_columns.sort(key=lambda x: x[0])
    
    base_dir = "processed_data"
    os.makedirs(base_dir, exist_ok=True)
    
    # Keep track of processed entries for logging
    processed_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        try:
            state = str(row['state']).strip()
            EAN = str(row['EAN']).strip()
            
            # Create state directory
            state_dir = os.path.join(base_dir, state)
            os.makedirs(state_dir, exist_ok=True)
            
            # Process coordinates
            listings = []
            for suffix, long_col in long_columns:
                long_val = row[long_col]
                if pd.isnull(long_val):
                    break
                
                # Get corresponding latitude column
                if using_generic_columns:
                    lat_col = 'Latitude'
                else:
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
                processed_count += 1
            
        except Exception as e:
            error_count += 1
            st.warning(f"Error processing row {index + 2} (EAN: {EAN}): {str(e)}")
            continue
    
    # Log processing summary
    st.info(f"Processing Summary:\n"
            f"- Successfully processed: {processed_count} entries\n"
            f"- Errors encountered: {error_count} entries")
    
    return base_dir

def main():
    st.title("PECS EA LISTING SPLITTER")
    
    # Add instructions
    st.write("""
    ### Instructions:
    1. Upload a CSV file containing state and EAN columns
    2. The file should also contain either:
       - Numbered longitude/latitude columns (location_gps-Longitude_1, location_gps-Latitude_1, etc.)
       - OR generic 'Latitude' and 'Longitude' columns
    3. Click the upload button below to process your file
    """)
    
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            with st.spinner('Processing your file...'):
                base_dir = process_csv(uploaded_file)
            
            st.success("Processing completed successfully!")
            
            # Create download button for the zip file
            zip_file = create_zip_file(base_dir)
            st.download_button(
                label="Download Split EAs",
                data=zip_file,
                file_name="Split_EAs.zip",
                mime="application/zip"
            )
            
            st.balloons()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
        
        finally:
            # Clean up the processed_data directory
            if 'base_dir' in locals():
                try:
                    shutil.rmtree(base_dir)
                except Exception as e:
                    st.warning(f"Warning: Could not clean up temporary files: {str(e)}")

if __name__ == "__main__":
    main()
