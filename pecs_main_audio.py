import streamlit as st
import pandas as pd
import io
import zipfile

st.title("Excel Audio & Question Extractor with ZIP Download")

st.markdown("""
This app extracts specific columns from an uploaded Excel file and creates new Excel files for each state.
**Process:**
- It always includes **InstanceID**, **state**, **EAN**, and **num_men**.
- It then extracts every column whose header contains **"audio"**.
- For each audio column, the corresponding question column is determined by removing the prefix **"audio_"** (if present) from its header.
- In the output file the order is:
  1. The common columns.
  2. For each audio column:
     - The audio column,
     - Its corresponding question column,
     - A blank column (headered **approval status**) with green fill and white text.
  3. A final column **Final Approval** is added at the end for final decision entry.
All the Excel files (one per state) will be grouped into a ZIP file.
""")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error("Error reading the Excel file: " + str(e))
        st.stop()

    # Check for required common columns.
    common_cols = ['instanceID', 'state', 'EAN', 'num_men']
    for col in common_cols:
        if col not in df.columns:
            st.error(f"Required column '{col}' not found in the uploaded file.")
            st.stop()

    # Identify audio columns (case insensitive).
    audio_columns = [col for col in df.columns if "audio" in col.lower()]
    if not audio_columns:
        st.warning("No audio columns found in the uploaded file.")
        st.stop()

    st.success("File successfully read. Processing...")

    # Dictionary to store each state's Excel file as bytes.
    excel_files = {}

    # Process the data by state.
    states = df['state'].unique()
    st.write(f"Found {len(states)} unique state(s): {', '.join(map(str, states))}")

    for state in states:
        # Filter the DataFrame for the current state.
        state_df = df[df['state'] == state]

        # Build the output DataFrame column by column.
        new_df = pd.DataFrame(index=state_df.index)

        # 1. Add the common columns.
        for col in common_cols:
            new_df[col] = state_df[col]

        # 2. For each audio column, add:
        #    - the audio column,
        #    - the corresponding question column (if available, else blank),
        #    - a blank approval status column (with a unique internal name).
        for audio_col in audio_columns:
            # Audio column.
            new_df[audio_col] = state_df[audio_col]

            # Determine the corresponding question column name.
            if audio_col.startswith("audio_"):
                question_col = audio_col[len("audio_"):]
            else:
                question_col = audio_col

            # Add the question column (or blank if it does not exist).
            if question_col in state_df.columns:
                new_df[question_col] = state_df[question_col]
            else:
                new_df[question_col] = ""

            # Create a unique internal name for the approval status column.
            approval_internal = f"approval status__{audio_col}"
            new_df[approval_internal] = ""

        # 3. Add the final approval column.
        new_df["Final Approval"] = ""

        # 4. Reorder columns to ensure the desired layout.
        #    Order: common columns, then for each audio: (audio, question, approval status) and finally Final Approval.
        ordered_cols = []
        ordered_cols.extend(common_cols)
        for audio_col in audio_columns:
            ordered_cols.append(audio_col)
            if audio_col.startswith("audio_"):
                question_col = audio_col[len("audio_"):]
            else:
                question_col = audio_col
            ordered_cols.append(question_col)
            ordered_cols.append(f"approval status__{audio_col}")
        ordered_cols.append("Final Approval")
        new_df = new_df[ordered_cols]

        # 5. Rename approval status columns to display the header "approval status".
        rename_map = {f"approval status__{audio_col}": "approval status" for audio_col in audio_columns}
        new_df.rename(columns=rename_map, inplace=True)

        # 6. Write the DataFrame to an Excel file with formatting.
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            new_df.to_excel(writer, index=False, sheet_name=str(state))
            workbook  = writer.book
            worksheet = writer.sheets[str(state)]

            # Create the format for the approval status cells: green fill, white text.
            approval_format = workbook.add_format({'bg_color': 'green', 'font_color': 'white'})

            # Apply the format to every column whose header is "approval status".
            for idx, header in enumerate(new_df.columns):
                if header == "approval status":
                    # Set the column format (default width is maintained).
                    worksheet.set_column(idx, idx, None, approval_format)

            writer.close()

        excel_buffer.seek(0)
        excel_files[f"{state}.xlsx"] = excel_buffer.getvalue()

    # 7. Create a ZIP file containing all the Excel files.
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
