import streamlit as st
import pandas as pd
import numpy as np
from pdf_utils import generate_pdf_from_dataframe
from pdf_converter import pdf_generator
# Assuming Table_formatting is a custom module, keep it if it's used elsewhere
# from Table_formatting import style_dataframe 

st.set_page_config(page_title="Rail Madad Data Analysis", layout="wide")
st.subheader("Rail Madad Data Analysis 👋")

with st.expander("Upload File"):
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

division_map = pd.DataFrame([
    ["BPT", "Mumbai Port Trust"], ["BR", "Bangladesh Rly"], ["CPT", "Calcutta Port Trust"],
    ["BB", "Mumbai"], ["BSL", "Bhusaval"], ["NGP", "Nagpur (CR)"], ["PUNE", "Pune"],
    ["SUR", "Solapur"], ["EDFC", "Eastern Dedicated Freight Corr"],
    ["WDFC", "Western Dedicated Freight Corr"], ["DDU", "Pt. Deen Dayal Upadhyaya"],
    ["MGS", "Pt. Deen Dayal Upadhyaya"], ["DHN", "Dhanbad"], ["DNR", "Danapur"],
    ["SEE", "Sonpur"], ["SPJ", "Samastipur"], ["KUR", "Khurda Road"], ["SBP", "Sambalpur"],
    ["WAT", "Waltair"], ["ASN", "Asansol"], ["HWH", "Howrah"], ["MLDT", "Malda"],
    ["SDAH", "Sealdah"], ["KAWR", "Karwar"], ["RN", "Ratnagiri"], ["AGRA", "Agra"],
    ["JHS", "Jhansi"], ["PRYJ", "Prayagraj"], ["ALD", "Prayagraj"], ["BSB", "Varanasi"],
    ["IZN", "Izzat Nagar"], ["LJN", "Lucknow"], ["APDJ", "Alipur Duar Jn"],
    ["KIR", "Katihar"], ["LMG", "Lumding"], ["RNY", "Rangiya"], ["TSK", "Tinsukia"],
    ["DLI", "Delhi"], ["FZR", "Firozpur"], ["LKO", "Lucknow"], ["MB", "Moradabad"],
    ["UMB", "Ambala"], ["AII", "Ajmer"], ["BKN", "Bikaner"], ["JP", "Jaipur"],
    ["JU", "Jodhpur"], ["PR", "Pakistan Rly"], ["PPBR", "Pipavav"], ["BZA", "Vijayawada"],
    ["GNT", "Guntur"], ["GTL", "Guntakal"], ["HYB", "Hyderabad"], ["NED", "Nanded"],
    ["SC", "Secunderabad"], ["ADRA", "Adra"], ["CKP", "Chakradhar Pur"],
    ["KGP", "Kharagpur"], ["RNC", "Ranchi"], ["BSP", "Bilaspur"], ["NAG", "Nagpur (SECR)"],
    ["R", "Raipur"], ["MAS", "Chennai"], ["MDU", "Madurai"], ["PGT", "Palghat"],
    ["SA", "Salem"], ["TPJ", "Tiruchchirapalli"], ["TVC", "Trivandrum Central"],
    ["MYS", "Mysore"], ["SBC", "Bangalore"], ["UBL", "Hubli"], ["BPL", "Bhopal"],
    ["JBP", "Jabalpur"], ["KOTA", "Kota"], ["ADI", "Ahmedabad"],
    ["BCT", "Mumbai Central (WR)"], ["BRC", "Vadodara"], ["BVC", "Bhavnagar"],
    ["BVP", "Bhavnagar"], ["RJT", "Rajkot"], ["RTM", "Ratlam"], ["CSTM", "Mumbai (CR)"],
    ["IRC", "IRCTC"], ["NORTH_ZONE", "NZ"], ["WEST_ZONE", "WZ"], ["SOUTH_ZONE", "SZ"],
    ["EAST_ZONE", "EZ"], ["SOUTH_CENTRAL_ZONE", "SCZ"], ["JAT", "Jammu"]
], columns=["Division", "Division Name"])

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
    "pnrUtsNo": "PNR UTS No"
}

def beautify_column(col):
    return rename_mapping.get(col, ''.join([' ' + c if c.isupper() else c for c in col]).strip().title())

def load_data(file):
    return pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file, engine='python', on_bad_lines='warn')

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[[col for col in columns_to_keep if col in df.columns]]
    df = df.rename(columns={col: beautify_column(col) for col in df.columns})

    if 'Train/Station' in df.columns:
        df['Train/Station'] = df['Train/Station'].astype(str)

    if 'PNR UTS No' in df.columns:
        df['PNR UTS No'] = df['PNR UTS No'].astype(str)
    
    with st.expander("Filters"):
        dropdown_fields = [
            "Ref No", "Mode", "Train/Station", "Channel", "Type", "Sub Type",
            "Zone", "Division", "Owning Zone", "Owning Division", "Department",
            "SLA", "Rating", "Status", "Forwarded", "PNR UTS No"
        ]
        filters = {}
        
        cols1 = st.columns(8)
        cols2 = st.columns(8)

        for i, field in enumerate(dropdown_fields):
            if field in df.columns:
                options = df[field].dropna().unique().tolist()
                if i < 8:
                    with cols1[i]:
                        selected = st.selectbox(f"Select {field}", ["All"] + sorted(map(str, options)), key=f"filter_{field}_row1")
                else:
                    with cols2[i-8]:
                        selected = st.selectbox(f"Select {field}", ["All"] + sorted(map(str, options)), key=f"filter_{field}_row2")
                
                if selected != "All":
                    filters[field] = selected

    # This st.text_input is now outside the expander, ensuring its scope
    search_term = st.text_input("Search in Complaint Description:", key="search_complaint_desc")

    filtered_df = df.copy()
    for col, val in filters.items():
        filtered_df = filtered_df[filtered_df[col].astype(str) == val]
        
    # Apply search filter outside the expander for consistency in data processing
    if search_term and "Complaint Desc" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Complaint Desc"].str.contains(search_term, case=False, na=False)]
        
    
    filtered_df = pd.merge(filtered_df, division_map, on="Division", how="left")
    condition = (
    (filtered_df['Division Name'].isna() | (filtered_df['Division Name'].str.strip() == "")) &
    (filtered_df['Division'] == "HQ")
    )

    filtered_df['Division Name'] = np.where(
        condition,
        filtered_df['Zone'] + "/HQ",
        filtered_df['Division Name']
    )
    filtered_df["Created On"] = pd.to_datetime(filtered_df["Created On"].astype(str).str.strip(), format="%d-%m-%y %H:%M", errors='coerce')
    filtered_df["Modified On"] = pd.to_datetime(filtered_df["Modified On"].astype(str).str.strip(), format="%d-%m-%y %H:%M", errors='coerce')

    filtered_df.to_csv("test.csv")

    filtered_df["Diff"] = filtered_df["Modified On"] - filtered_df["Created On"]
    filtered_df["TimeTakenMin"] = filtered_df["Diff"].dt.total_seconds() / 60
    filtered_df["MoreThan90Min"] = (filtered_df["TimeTakenMin"] >= 90).astype(int)
    filtered_df["IsSocialMedia"] = (filtered_df["Channel"] == "M").astype(int)
    filtered_df["MoreThan90Min_SM"] = ((filtered_df["MoreThan90Min"] == 1) & (filtered_df["IsSocialMedia"] == 1)).astype(int)
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
        filtered_df.groupby(['Zone', 'Division Name'], dropna=False)
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
    
    Social_Media_summary_filtered = Social_Media_summary_raw[Social_Media_summary_raw['Cases'] > 0].copy()

    Social_Media_summary = pd.DataFrame()
    for zone in Social_Media_summary_filtered['Zone'].unique():
        zone_df = Social_Media_summary_filtered[Social_Media_summary_filtered['Zone'] == zone].copy()
        
        zone_df = zone_df.sort_values(by='>90 Min Cases', ascending=False)
        
        zone_total = pd.DataFrame([{
            'Zone': zone,
            'Division Name': 'Total',
            'Cases': zone_df['Cases'].sum(),
            '>90 Min Cases': zone_df['>90 Min Cases'].sum()
        }])
        
        Social_Media_summary = pd.concat([Social_Media_summary, zone_df, zone_total], ignore_index=True)

    Social_Media_summary['Zone'] = Social_Media_summary['Zone'].astype(str)
    Social_Media_summary['Division Name'] = Social_Media_summary['Division Name'].astype(str)
    Social_Media_summary['Division Name'] = np.where(
    Social_Media_summary['Division Name'] == "nan"   ,
    Social_Media_summary['Zone'] + "/HQ",
    Social_Media_summary['Division Name'])
    


    with st.expander("Social Media Summary"):
        st.dataframe(Social_Media_summary) 
        pdf_buffer = generate_pdf_from_dataframe(
                                        Social_Media_summary, 
                                        filters="selection_info", 
                                        header_text="Social Media Reply"
                                    )
        st.download_button(
                                        label="📥 Download Zone/Division wise SM Report",
                                        data=pdf_buffer,
                                        file_name="summary_report.pdf",
                                        mime="application/pdf",
                                    )

    

    
    
    
    
        
    # Step 1: Categorize TimeTakenMin into bins
    conditions = [
    (filtered_df['TimeTakenMin'] <= 10),
    (filtered_df['TimeTakenMin'] > 10) & (filtered_df['TimeTakenMin'] <= 20),
    (filtered_df['TimeTakenMin'] > 20) & (filtered_df['TimeTakenMin'] <= 40),
    (filtered_df['TimeTakenMin'] > 40) & (filtered_df['TimeTakenMin'] <= 60),
    (filtered_df['TimeTakenMin'] > 60) & (filtered_df['TimeTakenMin'] <= 90),
    (filtered_df['TimeTakenMin'] > 90) & (filtered_df['TimeTakenMin'] <= 120),
    (filtered_df['TimeTakenMin'] > 120) & (filtered_df['TimeTakenMin'] <= 240),
    (filtered_df['TimeTakenMin'] > 240)
]

    labels = [
        "<=10 Min",
        "11-20 Min",
        "21-40 Min",
        "41-60 Min",
        "61-90 Min",
        "91-120 Min",
        "121-240",
        "> 240"
    ]

    filtered_df['TimeFreq'] = np.select(conditions, labels, default="Unknown")

    # Step 2: Filter out unknowns (optional)
    valid_df = filtered_df[filtered_df['TimeFreq'] != 'Unknown']
    print(len(valid_df))
    valid_df.to_csv("sdfgdfgdfh.csv")
    
        # Step 1: Crosstab
    zone_division_summary = pd.crosstab(
        index=[valid_df['Zone'], valid_df['Division Name']],
        columns=valid_df['TimeFreq']
    )


    # Step 2: Add row totals
    zone_division_summary['Total'] = zone_division_summary.sum(axis=1)

    # Step 3: Add column totals
    total_row = zone_division_summary.sum(numeric_only=True)
    total_row.name = ('Total', 'Total')  # Proper MultiIndex to match index
    zone_division_summary = pd.concat([zone_division_summary, total_row.to_frame().T])

    # Step 4: Reset index with proper column names
    zone_division_summary = zone_division_summary.reset_index()
    zone_division_summary = zone_division_summary.rename(columns={
        zone_division_summary.columns[0]: 'Zone',
        zone_division_summary.columns[1]: 'Division Name'
    })

    # Step 5: Optional: Remove columns.name and axis name
    zone_division_summary.columns.name = None
    zone_division_summary = zone_division_summary.rename_axis(None, axis=1)

    # Step 6: Show in Streamlit
    with st.expander("Zone and Division Wise Summary"):
        st.dataframe(zone_division_summary)
        pdf_buffer_Zone = pdf_generator(zone_division_summary, "")
        st.download_button(
                label="📥 Download Summary as PDF",
                data=pdf_buffer_Zone,
                file_name="summary_report.pdf",
                mime="application/pdf",
                key="download_pdf_button_final"
            )
    with st.expander("Complaint Wise Summary"):
        Type_summary = pd.crosstab(
            index=valid_df['Type'],
            columns=valid_df['TimeFreq']
        )

        desired_columns = ['<=10 Min', '11-20 Min', '21-40 Min', '41-60 Min', 
                        '61-90 Min', '91-120 Min', '121-240', '> 240']
        
        for col in desired_columns:
            if col not in Type_summary.columns:
                Type_summary[col] = 0

        Type_summary = Type_summary[desired_columns]
        Type_summary['Total'] = Type_summary.sum(axis=1)

        total_row_type = Type_summary.sum(numeric_only=True)
        total_row_type.name = 'Total'
        Type_summary = pd.concat([Type_summary, total_row_type.to_frame().T])

        Type_summary = Type_summary.reset_index()
        Type_summary = Type_summary.rename(columns={Type_summary.columns[0]: 'Complaint Type'})

        Type_summary_no_total = Type_summary[Type_summary['Complaint Type'] != 'Total']
        total_row_df = Type_summary[Type_summary['Complaint Type'] == 'Total']

        Type_summary_sorted = pd.concat([
            Type_summary_no_total.sort_values(by='Total', ascending=False),
            total_row_df
        ], ignore_index=True)

        st.dataframe(Type_summary_sorted)
        pdf_buffer_Type = pdf_generator(Type_summary_sorted, "")
        st.download_button(
            label="📥 Complaint Type",
            data=pdf_buffer_Type,
            file_name="Type_summary.pdf",
            mime="application/pdf",
            key="download_pdf_button_final_type"
        )

    
    st.write(f"Showing {len(filtered_df)} filtered results")
    st.dataframe(filtered_df)
