import streamlit as st
import pandas as pd
import io
import zipfile

st.title("Excel Audio & Question Extractor with ZIP Download")

st.markdown("""
This app extracts specific columns from an uploaded Excel file and creates new Excel files for each state.  
**Process:**  
- The app expects the first two rows of the uploaded Excel file to be header rows:  
  - **Row 1:** Variable names (e.g., InstanceID, state, audio_..., etc.)  
  - **Row 2:** Variable labels  
- It always includes **InstanceID**, **state**, **EAN**, and **num_men**.  
- It then extracts every column whose header contains **"audio"** (case insensitive).  
- For each audio column, the corresponding question column is determined by removing the prefix **"audio_"** from its header.  
- For each audio group, the output file will contain:  
  1. The audio column  
  2. Its corresponding question column (with its variable label from row 2, if available)  
  3. A new blank column titled **approval status** (only its header cell in row 1 is colored green with white text)  
- Finally, a **Final Approval** column is added at the end (with a two‑row header where the second row is blank).  
- All state‑specific Excel files are grouped into one ZIP file for download.
""")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Read the file with two header rows (row 0 and row 1)
        df = pd.read_excel(uploaded_file, header=[0, 1])
    except Exception as e:
        st.error("Error reading the Excel file: " + str(e))
        st.stop()

    # Helper to retrieve a column tuple from the MultiIndex based on the first level
    def get_column_by_first_level(df, name):
        for col in df.columns:
            if col[0] == name:
                return col
        return None

    # Check for required common columns.
    common_cols = ['instanceID', 'state', 'EAN', 'num_men']
    common_col_tuples = {}
    for col in common_cols:
        col_tuple = get_column_by_first_level(df, col)
        if col_tuple is None:
            st.error(f"Required column '{col}' not found in the uploaded file.")
            st.stop()
        common_col_tuples[col] = col_tuple

    # Identify audio columns (where the first-level header contains "audio")
    audio_col_tuples = [col for col in df.columns if "audio" in col[0].lower()]
    if not audio_col_tuples:
        st.warning("No audio columns found in the uploaded file.")
        st.stop()

    # Get unique states from the 'state' column.
    state_col = common_col_tuples['state']
    states = df[state_col].unique()
    st.write(f"Found {len(states)} unique state(s): {', '.join(map(str, states))}")

    # Dictionary to store Excel files for each state.
    excel_files = {}

    for state in states:
        state_df = df[df[state_col] == state].copy()

        # Build the new DataFrame column by column with a MultiIndex (2 header rows).
        new_columns = []
        new_data = {}

        # 1. Add common columns in the specified order.
        for col in common_cols:
            tup = common_col_tuples[col]
            new_columns.append(tup)
            new_data[tup] = state_df[tup]

        # 2. For each audio column, add:
        #    - the audio column, 
        #    - its corresponding question column (if exists; else create a blank column),
        #    - a new approval status column (with header ("approval status", "") )
        for audio_tup in audio_col_tuples:
            # Audio column (from the original file, so both header rows are retained)
            new_columns.append(audio_tup)
            new_data[audio_tup] = state_df[audio_tup]

            # Determine corresponding question column by removing "audio_" (if present)
            audio_name = audio_tup[0]
            if audio_name.lower().startswith("audio_"):
                question_name = audio_name[len("audio_"):]
            else:
                question_name = audio_name
            question_tup = get_column_by_first_level(df, question_name)
            if question_tup in state_df.columns:
                new_columns.append(question_tup)
                new_data[question_tup] = state_df[question_tup]
            else:
                # If not found, create a new blank column with header (question_name, "")
                new_tup = (question_name, "")
                new_columns.append(new_tup)
                new_data[new_tup] = pd.Series([""] * len(state_df), index=state_df.index)

            # Add new blank approval status column with a two-row header.
            approval_tup = ("approval status", "")
            new_columns.append(approval_tup)
            new_data[approval_tup] = pd.Series([""] * len(state_df), index=state_df.index)

        # 3. Append the Final Approval column at the end.
        final_approval_tup = ("Final Approval", "")
        new_columns.append(final_approval_tup)
        new_data[final_approval_tup] = pd.Series([""] * len(state_df), index=state_df.index)

        # Create the new DataFrame with the specified column order.
        new_df = pd.DataFrame(new_data, columns=new_columns)

        # Write the new DataFrame to an Excel file using xlsxwriter.
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            new_df.to_excel(writer, index=False, sheet_name=str(state))
            workbook = writer.book
            worksheet = writer.sheets[str(state)]

            # Create the header format for approval status cells (only top header row).
            approval_format = workbook.add_format({'bg_color': 'green', 'font_color': 'white'})

            # For multi-index headers, the top header row is at row 0.
            # Overwrite the header cell in row 0 for every "approval status" column.
            for col_num, col_tuple in enumerate(new_df.columns):
                if col_tuple[0] == "approval status":
                    worksheet.write(0, col_num, "approval status", approval_format)
            writer.close()
        output.seek(0)
        excel_files[f"{state}.xlsx"] = output.getvalue()

    # Create a ZIP file containing all the state-specific Excel files.
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, filebytes in excel_files.items():
            zip_file.writestr(filename, filebytes)
    zip_buffer.seek(0)

    st.download_button(
        label="Download All Excel Files as ZIP",
        data=zip_buffer,
        file_name="state_excel_files.zip",
        mime="application/zip"
    )
    st.success("Processing complete!")
