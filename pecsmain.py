import streamlit as st
import pandas as pd
import io
import zipfile
import os

st.title("PECS MAIN Splitter with Folder Grouping")

# Allow the user to upload either a CSV or XLSX file
uploaded_file = st.file_uploader("Upload your CSV or XLSX file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Determine file type by extension and read accordingly
        filename = uploaded_file.name
        _, ext = os.path.splitext(filename)
        if ext.lower() == ".csv":
            df = pd.read_csv(uploaded_file)
        elif ext.lower() in [".xls", ".xlsx"]:
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type!")
            df = None

        if df is not None:
            st.write("### Data Preview")
            st.dataframe(df.head())
    except Exception as e:
        st.error(f"Error reading the file: {e}")
        df = None

    if df is not None:
        # Let the user pick the column to split the data into separate CSV files.
        split_column = st.selectbox(
            "Select the column to split the data into separate CSV files",
            options=df.columns
        )

        # Let the user pick the column to group the CSV files into folders (e.g. state).
        grouping_column = st.selectbox(
            "Select the column to group the CSV files into folders (e.g. state)",
            options=df.columns
        )

        if st.button("Generate Zipped CSV Files"):
            # Create an in-memory BytesIO buffer for the ZIP archive.
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                # Iterate over unique values in the grouping column (folder names)
                for group_value in df[grouping_column].dropna().unique():
                    # Filter the DataFrame for the current group (e.g. state)
                    df_group = df[df[grouping_column] == group_value]

                    # Within this group, iterate over unique values in the splitting column.
                    for split_value in df_group[split_column].dropna().unique():
                        # Filter the group for the current split value.
                        df_split = df_group[df_group[split_column] == split_value]

                        # Convert the subset DataFrame to CSV bytes (without the index)
                        csv_bytes = df_split.to_csv(index=False).encode("utf-8")

                        # Create safe folder and file names by replacing spaces with underscores.
                        folder_name = str(group_value).replace(" ", "_")
                        file_name = f"{str(split_value).replace(' ', '_')}.csv"

                        # Define the file path within the ZIP archive (folder/file structure)
                        zip_path = f"{folder_name}/{file_name}"

                        # Write the CSV file into the ZIP archive.
                        zip_file.writestr(zip_path, csv_bytes)

            # Reset the buffer's current position to the beginning.
            zip_buffer.seek(0)

            st.success("Zipped file generated successfully!")
            # Provide a download button for the ZIP archive.
            st.download_button(
                label="Download Zipped CSV Files",
                data=zip_buffer,
                file_name="split_csvs.zip",
                mime="application/zip"
            )

              st.ballon()
