import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import tempfile
import os

st.title("RH XML Viewer and CSV Exporter")

uploaded_files = st.file_uploader("Upload XML files with <RH> records", type="xml", accept_multiple_files=True)

# Dropdown options for Reservation Status
status_options = ["", "CHECKED OUT", "RESERVED", "CANCELLED", "NO SHOW"]

# Filter UI
col1, col2 = st.columns(2)
with col1:
    status_filter = st.selectbox("Filter by RS (Status)", options=status_options)
    rid_filter = st.text_input("Filter by RID (Reservation ID, optional):").strip()
with col2:
    begin_date = st.date_input("BD (Check-in) on or after (optional)", value=None)
    end_date = st.date_input("ED (Check-out) on or before (optional)", value=None)

stay_date = st.date_input("Stay Date (must fall between BD & ED, optional)", value=None)

results = []

if uploaded_files:
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            tree = ET.parse(tmp_path)
            root = tree.getroot()
        except Exception as e:
            st.error(f"Error parsing file {uploaded_file.name}: {e}")
            continue
        finally:
            os.unlink(tmp_path)

        for rh in root.findall(".//RH"):
            attributes = rh.attrib
            rs = attributes.get("RS")
            rid = attributes.get("RID")
            bd = attributes.get("BD")
            ed = attributes.get("ED")

            try:
                bd_date = datetime.strptime(bd, "%Y-%m-%d").date() if bd else None
                ed_date = datetime.strptime(ed, "%Y-%m-%d").date() if ed else None
            except Exception as e:
                st.warning(f"Skipping <RH> entry due to date format error in {uploaded_file.name}: {e}")
                continue

            match_status = not status_filter or (rs and rs.upper() == status_filter)
            match_rid = not rid_filter or (rid and rid == rid_filter)
            match_bd = not begin_date or (bd_date and bd_date >= begin_date)
            match_ed = not end_date or (ed_date and ed_date <= end_date)
            match_stay = not stay_date or (bd_date and ed_date and bd_date <= stay_date <= ed_date)

            if match_status and match_rid and match_bd and match_ed and match_stay:
                results.append(attributes)

    if results:
        df = pd.DataFrame(results)
        st.success(f"{len(results)} matching <RH> entries found.")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="filtered_rh_entries.csv",
            mime="text/csv"
        )
    else:
        st.warning("No matching entries found.")
