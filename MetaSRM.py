import streamlit as st
import pandas as pd
import numpy as np
from pdf_utils import generate_pdf_from_dataframe
from Table_formatting import style_dataframe

st.set_page_config(page_title="Rail Madad Data Analysis", layout="wide")
st.subheader("Rail Madad Data Analysis 👋")

with st.expander("Upload File"):
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

columns_to_keep = [
    "complaintRefNo", "createdOn", "modifiedOn", "complaintMode", "trainStation", "channelType",
    "compTypeName", "subTypeName", "zoneCode", "divCode", "ownZoneCode", "deptCode",
    "sla", "rating", "status", "diff", "ownDivCode", "commodity", "forwarded",
    "pnrUtsNo", "coachType", "coachNo", "feedbackRemark", "nextStation", "contactId",
    "physicalCoachNo", "trainNameForReport", "complaintDesc", "remarks", "userId",
    "userMobile", "Coach Owning Railway"
]

rename_mapping = {
    "complaintRefNo": "Ref No",
    "createdOn": "Created On",
    "modifiedOn": "Modified On",
    "complaintMode": "Mode",
    "trainStation": "Train/Station",
    "channelType": "Channel",
    "compTypeName": "Type",
    "subTypeName": "Sub Type",
    "zoneCode": "Zone",
    "divCode": "Division",
    "ownZoneCode": "Owning Zone",
    "ownDivCode": "Owning Division",
    "deptCode": "Department",
    "sla": "SLA",
    "rating": "Rating",
    "status": "Status",
    "forwarded": "Forwarded",
}

def beautify_column(col):
    return rename_mapping.get(col, ''.join([' ' + c if c.isupper() else c for c in col]).strip().title())

def load_data(file):
    return pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[[col for col in columns_to_keep if col in df.columns]]
    df = df.rename(columns={col: beautify_column(col) for col in df.columns})

    # --- FIX FOR ArrowTypeError: Convert 'Train/Station' to string type ---
    if 'Train/Station' in df.columns:
        df['Train/Station'] = df['Train/Station'].astype(str)
    # --- END FIX ---

    st.sidebar.header("Filter Options")
    dropdown_fields = ["Ref No", "Mode", "Train/Station", "Channel", "Type", "Sub Type",
                       "Zone", "Division", "Owning Zone", "Owning Division", "Department",
                       "SLA", "Rating", "Status", "Forwarded"]

    filters = {}
    for field in dropdown_fields:
        if field in df.columns:
            options = df[field].dropna().unique().tolist()
            selected = st.sidebar.selectbox(f"Select {field}", ["All"] + sorted(map(str, options)))
            if selected != "All":
                filters[field] = selected

    search_term = st.text_input("Search in Complaint Description:")

    filtered_df = df.copy()
    for col, val in filters.items():
        filtered_df = filtered_df[filtered_df[col].astype(str) == val]

    if search_term and "Complaint Desc" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Complaint Desc"].str.contains(search_term, case=False, na=False)]
    

    filtered_df["Created On"] = pd.to_datetime(filtered_df["Created On"].astype(str).str.strip(), format="%d-%m-%y %H:%M", errors='coerce')
    filtered_df["Modified On"] = pd.to_datetime(filtered_df["Modified On"].astype(str).str.strip(), format="%d-%m-%y %H:%M", errors='coerce')

    filtered_df.to_csv("test.csv")

    filtered_df["Diff"] = filtered_df["Modified On"] - filtered_df["Created On"]
    filtered_df["TimeTakenMin"] = filtered_df["Diff"].dt.total_seconds() / 60
    filtered_df["MoreThan90Min"] = (filtered_df["TimeTakenMin"] >= 90).astype(int)
    filtered_df["IsSocialMedia"] = (filtered_df["Channel"] == "M").astype(int)
    filtered_df["MoreThan90Min_SM"] = ((filtered_df["MoreThan90Min"] == 1) & (filtered_df["IsSocialMedia"] == 1)).astype(int)

    st.header("Scorecard")
    col1, col2, col3, col4, col5 = st.columns(5)

    total_cases = len(filtered_df)
    closed = filtered_df["Diff"].notna().sum()
    open_cases = filtered_df["Modified On"].isna().sum()
    train_cases = (filtered_df["Mode"] == "T").sum()
    station_cases = (filtered_df["Mode"] == "S").sum()
    SLA1 = (filtered_df["SLA"] == "SLA 1").sum()
    SLA2 = (filtered_df["SLA"] == "SLA 2").sum()
    Unsatisfactory = (filtered_df["Rating"] == "Unsatisfactory").sum()
    Satisfactory = (filtered_df["Rating"] == "Satisfactory").sum()
    Excellent = (filtered_df["Rating"] == "Excellent").sum()
    No_Feedback = filtered_df["Rating"].isna().sum()

    def styled_metric(title, value, color="#f0f2f6"):
        st.markdown(
            f"""
            <div style="background-color: {color}; padding: 10px; border-radius: 10px; text-align: center; height: 80px;">
                <div style="font-size: 14px; margin-bottom: 4px; font-weight: 600;">{title}</div>
                <div style="font-size: 20px; font-weight: bold; color: #31333f;">{value}</div>
            </div>
            """, unsafe_allow_html=True
        )

    def pct(count):
        return f"{(count / total_cases * 100):.0f}%" if total_cases else "0%"

    with col1:
        styled_metric("Received/Closed/Open", f'{total_cases}/{closed}/{open_cases}', "#fce4ec")
    with col2:
        styled_metric("Train/Station", f'{train_cases}/{station_cases}', "#fff3e0")
    with col3:
        styled_metric("SLA1/SLA2", f'{SLA1}/{SLA2}', "#ede7f6")
    with col4:
        styled_metric("Excellent/Satisfactory", f"{Excellent} ({pct(Excellent)}) / {Satisfactory} ({pct(Satisfactory)})", "#e8f5e9")
    with col5:
        styled_metric("Unsatisfactory/No_Feedback", f"{Unsatisfactory} ({pct(Unsatisfactory)}) / {No_Feedback} ({pct(No_Feedback)})", "#fce4ec")
        
    Social_Media_summary_raw = (
        filtered_df.groupby(['Zone', 'Division'], dropna=False)
        .agg({
            'IsSocialMedia': 'sum',
            'MoreThan90Min_SM': 'sum'
        })
        .rename(columns={
            'IsSocialMedia': 'Cases',
            'MoreThan90Min_SM': '>90 Min Cases'
        })
        .reset_index()
    )
    
    # --- Modifications for Social_Media_summary ---
    
    # 3. Exclude where Cases = 0
    Social_Media_summary_filtered = Social_Media_summary_raw[Social_Media_summary_raw['Cases'] > 0].copy()

    # 2. Group By Zone, Sort by >90 Min cases (Largest to smallest)
    # 4. Add total Just after each Zone
    Social_Media_summary = pd.DataFrame()
    for zone in Social_Media_summary_filtered['Zone'].unique():
        zone_df = Social_Media_summary_filtered[Social_Media_summary_filtered['Zone'] == zone].copy()
        
        # Sort by '>90 Min Cases' within each zone
        zone_df = zone_df.sort_values(by='>90 Min Cases', ascending=False)
        
        # Calculate zone total
        zone_total = pd.DataFrame([{
            'Zone': zone,
            'Division': 'Total',
            'Cases': zone_df['Cases'].sum(),
            '>90 Min Cases': zone_df['>90 Min Cases'].sum()
        }])
        
        Social_Media_summary = pd.concat([Social_Media_summary, zone_df, zone_total], ignore_index=True)

    # 1. In Social_Media_summary I want to merge Zone when exporting pdf 
    # For PDF, the 'Zone' column can be merged by setting the same 'Zone' value to an empty string for subsequent rows
    # within the same zone after the first occurrence, which the PDF generation needs to handle for visual merging.
    # We will handle the merging visually in `pdf_utils.py` by checking for duplicate `Zone` values and
    # making them empty string for all but the first entry in a block, and then adding row spans.
    # For the Streamlit display, we can keep 'Zone' column as is or modify it for better visual grouping.
    # Here, let's keep it as is for Streamlit and handle the "merging" logic within the PDF generation.
    # The 'Total' row's Zone will already be present, which is correct.
    
    pdf_buffer = generate_pdf_from_dataframe(
                                Social_Media_summary, filters="selection_info"
                            )
    st.download_button(
                                label="📥 Download Zone/Division wise SM Report",
                                data=pdf_buffer,
                                file_name="summary_report.pdf",
                                mime="application/pdf",
                            )


    st.subheader("Zone-Division Summary")
    st.dataframe(Social_Media_summary) # This is where the error likely originates for the Streamlit display
    
    
    st.write(f"Showing {len(filtered_df)} filtered results")
    st.dataframe(filtered_df)