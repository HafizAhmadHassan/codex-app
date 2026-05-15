import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CSV Delta Generator", layout="wide")

st.title("CSV Difference Processor")

st.write("""
Upload:
- Old CSV File
- New CSV File

The app will:
1. Detect new rows
2. Detect modified rows
3. Detect deleted rows
""")

old_file = st.file_uploader("Upload OLD CSV", type=["csv"], key="old")
new_file = st.file_uploader("Upload NEW CSV", type=["csv"], key="new")

KEY_COLUMNS = ["user_info.tax_code", "user_info.vat_number"]

if old_file and new_file:

    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)

    # Validate keys
    missing_old = [c for c in KEY_COLUMNS if c not in old_df.columns]
    missing_new = [c for c in KEY_COLUMNS if c not in new_df.columns]

    if missing_old or missing_new:
        st.error(f"Missing key columns.\nOld Missing: {missing_old}\nNew Missing: {missing_new}")
        st.stop()

    # Fill NaN for comparison
    old_df = old_df.fillna("")
    new_df = new_df.fillna("")

    # Create composite key
    old_df["_key"] = old_df[KEY_COLUMNS].astype(str).agg("||".join, axis=1)
    new_df["_key"] = new_df[KEY_COLUMNS].astype(str).agg("||".join, axis=1)

    old_dict = old_df.set_index("_key").to_dict(orient="index")
    new_dict = new_df.set_index("_key").to_dict(orient="index")

    result_rows = []

    today = datetime.today().strftime("%Y-%m-%d")

    # -------------------------
    # NEW + MODIFIED RECORDS
    # -------------------------
    for key, new_row in new_dict.items():

        # New Row
        if key not in old_dict:
            row = dict(new_row)
            row["change_type"] = "NEW"
            result_rows.append(row)

        else:
            old_row = old_dict[key]

            # Compare excluding helper column
            changed = False

            for col in new_df.columns:
                if col == "_key":
                    continue

                old_val = str(old_row.get(col, ""))
                new_val = str(new_row.get(col, ""))

                if old_val != new_val:
                    changed = True
                    break

            if changed:
                row = dict(new_row)
                row["change_type"] = "MODIFIED"
                result_rows.append(row)

    # -------------------------
    # DELETED RECORDS
    # -------------------------
    for key, old_row in old_dict.items():

        if key not in new_dict:

            deleted_row = dict(old_row)

            deleted_row["closed_at"] = today
            deleted_row["is_active"] = False
            deleted_row["change_type"] = "DELETED"

            result_rows.append(deleted_row)

    # -------------------------
    # RESULT
    # -------------------------
    if result_rows:

        result_df = pd.DataFrame(result_rows)

        # Remove helper column
        if "_key" in result_df.columns:
            result_df = result_df.drop(columns=["_key"])

        st.success(f"{len(result_df)} changed rows detected")

        st.dataframe(result_df, use_container_width=True)

        csv_data = result_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Result CSV",
            data=csv_data,
            file_name="result.csv",
            mime="text/csv"
        )

    else:
        st.info("No differences detected.")