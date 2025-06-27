import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import warnings
import io

# Streamlit config
st.set_page_config(page_title="Ticket Actions Report", page_icon="📈", layout="wide")
warnings.filterwarnings('ignore')

# Custom CSS Styling
st.markdown("""
    <style>
        #MainMenu, .stDeployButton, footer, #stDecoration {visibility: hidden;}
        body { color: #FAFAFA; }
        h1, h2, h3, h4, h5, h6 { color: #4CAF50; text-align: center; }
        .streamlit-expanderHeader {
            background-color: #333333; color: #FFFFFF; border-radius: 5px; padding: 10px; margin-bottom: 10px; font-size: 1.2em;
        }
        .streamlit-expanderContent {
            background-color: #262626; border-radius: 5px; padding: 15px; margin-bottom: 10px;
        }
        div[data-testid="stInfo"] {
            background-color: #283747; color: #D4EDDA; border-left: 5px solid #28A745; padding: 10px; border-radius: 5px;
        }
        .stSelectbox, .stSelectbox > div > div, .stSelectbox > div > div > div > div {
            background-color: #333333; color: #FAFAFA;
        }
        .stDataFrame { background-color: #262626; color: #FAFAFA; }
        [data-testid="stMetric"] {
            background-color: #262626; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); display: flex; flex-direction: column; justify-content: space-between;
        }
        [data-testid="stMetricLabel"] { color: #ADD8E6; font-size: 0.9rem; margin-bottom: 0.5rem; }
        [data-testid="stMetricValue"] { color: #FFFFFF; font-size: 2rem; font-weight: bold; }
        [data-testid="stMetricDelta"] { color: #90EE90; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

st.subheader("📊 Indian Railways Ticket Actions Report")

uploaded_file = st.file_uploader("📂 Upload your main CSV or Excel file", type=["csv", "xlsx"], key="main_upload")
uploaded_fileFLR = st.file_uploader("📂 Upload your FLR CSV or Excel file (optional)", type=["csv", "xlsx"], key="flr_upload")

@st.cache_data
def load_data(file_input):
    df = pd.DataFrame()
    if file_input is not None:
        file_extension = file_input.name.split('.')[-1].lower()
        if file_extension == 'csv':
            st.info("Loading data from uploaded CSV file...")
            try:
                s_io = io.StringIO(file_input.getvalue().decode('utf-8'))
                df = pd.read_csv(s_io)
            except UnicodeDecodeError:
                try:
                    s_io = io.StringIO(file_input.getvalue().decode('ISO-8859-1'))
                    df = pd.read_csv(s_io)
                except Exception as e:
                    st.error(f"❌ Error reading uploaded CSV: {e}")
                    return pd.DataFrame()
        elif file_extension == 'xlsx':
            st.info("Loading data from uploaded Excel file.")
            try:
                df = pd.read_excel(file_input)
            except Exception as e:
                st.error(f"❌ Error reading uploaded Excel file: {e}")
                return pd.DataFrame()
        else:
            st.warning("⚠️ Unsupported file type. Please upload CSV or XLSX.")
            return pd.DataFrame()
    else:
        st.warning("⚠️ No file provided. Please upload a file.")
        return pd.DataFrame()
    return df

# Load datasets
data = pd.DataFrame()
if uploaded_file is not None:
    data = load_data(uploaded_file)
else:
    st.error("❗ Please upload a main CSV or Excel file to proceed.")
    st.stop()

data_FLR = pd.DataFrame()
AgentFLR_Summary = pd.DataFrame()

if uploaded_fileFLR is not None:
    data_FLR = load_data(uploaded_fileFLR)
    if not data_FLR.empty:
        # Rename columns for consistency
        data_FLR = data_FLR.rename(columns={'AgentName': 'agent_name', 'Ticket Created On': 'ticket_open_datetime'})
        data_FLR.columns = (data_FLR.columns.str.strip()
                           .str.replace('\xa0', ' ')
                           .str.replace('\u200b', '')
                           .str.replace(r'\s+', ' ', regex=True)
                           .str.lower()
                           .str.replace(' ', '_'))
        if "last_agent_flr" in data_FLR.columns and "ticket_open_datetime" in data_FLR.columns:
            data_FLR["last_agent_flr"] = pd.to_timedelta(data_FLR["last_agent_flr"], errors='coerce')
            data_FLR["ticket_open_datetime"] = pd.to_datetime(data_FLR["ticket_open_datetime"], format="%d/%m/%Y %I:%M:%S %p", errors='coerce')
            if data_FLR["last_agent_flr"].isnull().any():
                st.warning("Some rows in 'Last Agent FLR' could not be parsed and were set to NaT.")
            if data_FLR["ticket_open_datetime"].isnull().any():
                st.warning(f"{data_FLR['ticket_open_datetime'].isnull().sum()} rows in 'Ticket Created On' could not be parsed and were set to NaT.")
            data_FLR["flr_min"] = data_FLR["last_agent_flr"].dt.total_seconds() / 60
            data_FLR["flr_>_15_min"] = np.where(data_FLR["flr_min"] > 15, 1, 0)
            if 'agent_name' in data_FLR.columns:
                AgentFLR_Summary = pd.pivot_table(
                    data=data_FLR, index='agent_name', values='flr_>_15_min', aggfunc='sum',
                    margins=True, margins_name='Total', fill_value=0
                ).reset_index()
                AgentFLR_Summary = AgentFLR_Summary[AgentFLR_Summary['agent_name'] != 'Total']
            else:
                st.warning("⚠️ 'agent_name' column not found in FLR file.")
        else:
            missing = [col for col in ["last_agent_flr", "ticket_open_datetime"] if col not in data_FLR.columns]
            st.warning(f"⚠️ Missing columns in FLR file: {', '.join(missing)}.")
    else:
        st.warning("⚠️ FLR file is empty. Please check the file content.")
else:
    st.info("Please upload an FLR file for 'FLR > 15 Min' analysis.")

if data.empty:
    st.error("❗ No data loaded. Please upload a main CSV or Excel file.")
    st.stop()

# Clean column names in main data
data.columns = (data.columns.str.strip()
                .str.replace('\xa0', ' ')
                .str.replace('\u200b', '')
                .str.replace(r'\s+', ' ', regex=True)
                .str.lower()
                .str.replace(' ', '_'))

# Mapping for display names
internal_to_display_mapping = {
    'ticket_id': 'Ticket ID',
    'action': 'Action',
    'action_description': 'Action Description',
    'channel': 'Channel',
    'brand_name': 'Brand Name',
    'screen_name': 'Screen Name',
    'url': 'URL',
    'ticket_open_datetime': 'Ticket Open DateTime',
    'resolution_time': 'Resolution Time',
    'time_of_action': 'Time of action',
    'agent_name': 'Agent Name',
    'username': 'UserName'
}

# Verify required columns
required_columns = list(internal_to_display_mapping.keys())
missing_columns = [col for col in required_columns if col not in data.columns]
if missing_columns:
    st.error(f"🚫 Missing critical columns: {', '.join(missing_columns)}")
    st.error(f"Current columns: {data.columns.tolist()}")
    st.stop()

# Parse datetime fields
data['time_of_action'] = pd.to_datetime(data['time_of_action'], errors='coerce', dayfirst=True)
data['ticket_open_datetime'] = pd.to_datetime(data['ticket_open_datetime'], errors='coerce', dayfirst=True)
data['resolution_time'] = pd.to_datetime(data['resolution_time'], errors='coerce', dayfirst=True)

# Agent-wise Analysis
with st.expander("👤 Agent-wise Analysis", expanded=True):
    st.markdown("### 📈 Agent Performance Summary")
    agent_df = data[data['agent_name'].notna() & (data['agent_name'].str.lower() != 'system')].copy()
    ticket_counts = data['ticket_id'].value_counts()
    close_map = ticket_counts.apply(lambda x: 'Direct Close' if x == 3 else 'Agent Close')
    agent_df['Close Type'] = agent_df['ticket_id'].map(close_map)
    agent_df = agent_df.sort_values(['agent_name', 'time_of_action'])
    agent_df['Idle Time'] = agent_df.groupby('agent_name')['time_of_action'].diff().fillna(pd.Timedelta(seconds=0))
    agent_df['Idle Minutes'] = agent_df['Idle Time'].dt.total_seconds() / 60

    total_unique_tickets = data['ticket_id'].nunique()
    total_actions = len(data)
    valid_resolution_times = data['resolution_time'].dropna()
    valid_open_times = data['ticket_open_datetime'].dropna()
    avg_resolution_time_str = "N/A"
    if not valid_resolution_times.empty and not valid_open_times.empty:
        avg_resolution_time = (valid_resolution_times - valid_open_times.loc[valid_resolution_times.index]).mean()
        if not pd.isna(avg_resolution_time):
            avg_resolution_time_str = str(avg_resolution_time).split('.')[0]
    ticket_counts_overall = data['ticket_id'].value_counts()
    DC = ticket_counts_overall[ticket_counts_overall == 3].count()
    AC = ticket_counts_overall[ticket_counts_overall != 3].count()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Unique Tickets", f"{total_unique_tickets:,}")
    col2.metric("Total Actions Recorded", f"{total_actions:,}")
    col3.metric("Direct Close", f"{DC}")
    col4.metric("Agent Close", f"{AC}")

    st.markdown("#### 📊 Combined Agent Performance & Idle Time Distribution")
    summary_metrics = agent_df.groupby('agent_name').agg(
        Total_Tickets=('ticket_id', 'nunique'),
        Direct_Close=('ticket_id', lambda x: x[agent_df.loc[x.index, 'Close Type'] == 'Direct Close'].nunique()),
        Agent_Close=('ticket_id', lambda x: x[agent_df.loc[x.index, 'Close Type'] == 'Agent Close'].nunique()),
        Avg_Idle_Time_Minutes=('Idle Minutes', 'mean'),
        Max_Idle_Time_Minutes=('Idle Minutes', 'max')
    ).reset_index()

    if not AgentFLR_Summary.empty:
        final_summary = summary_metrics.merge(AgentFLR_Summary[['agent_name', 'flr_>_15_min']], on='agent_name', how='left')
        final_summary['flr_>_15_min'] = final_summary['flr_>_15_min'].fillna(0).astype(int)
    else:
        final_summary = summary_metrics.copy()
        final_summary['flr_>_15_min'] = 0

    final_summary['Avg_Idle_Time_Minutes'] = final_summary['Avg_Idle_Time_Minutes'].round(2)
    final_summary['Max_Idle_Time_Minutes'] = final_summary['Max_Idle_Time_Minutes'].round(2)

    bins = [0, 5, 10, 15, 20, 25, 30, 180, np.inf]
    labels = ['0-5 min', '6-10 min', '11-15 min', '16-20 min', '21-25 min', '26-30 min', '30-180 min', '180+ min (Long Gap)']
    agent_df['Idle Bucket for Distribution'] = pd.cut(agent_df['Idle Minutes'], bins=bins, labels=labels, right=True)
    idle_dist_pivot = agent_df.groupby(['agent_name', 'Idle Bucket for Distribution']).size().unstack(fill_value=0).reset_index()
    combined_summary_report = pd.merge(final_summary, idle_dist_pivot, on='agent_name', how='left')
    combined_summary_report.rename(columns={'agent_name': 'Agent Name', 'flr_>_15_min': 'FLR > 15 Min'}, inplace=True)

    column_config_dict = {
        'Agent Name': st.column_config.Column("Agent Name", help="Name of the agent", width="medium"),
        "Total_Tickets": st.column_config.NumberColumn("Total Tickets", help="Total unique tickets handled", format="%d"),
        "Direct_Close": st.column_config.NumberColumn("Direct Close", help="Tickets closed directly (3 actions)", format="%d"),
        "Agent_Close": st.column_config.NumberColumn("Agent Close", help="Tickets closed by agent (>3 actions)", format="%d"),
        "Avg_Idle_Time_Minutes": st.column_config.ProgressColumn("Avg. Idle (min)", help="Average idle time", format="%.2f", min_value=0, max_value=combined_summary_report['Max_Idle_Time_Minutes'].max()),
        "Max_Idle_Time_Minutes": st.column_config.ProgressColumn("Max Idle (min)", help="Maximum idle time", format="%.2f", min_value=0, max_value=combined_summary_report['Max_Idle_Time_Minutes'].max()),
        "FLR > 15 Min": st.column_config.NumberColumn("FLR > 15 Min", help="First Last Response > 15 minutes", format="%d")
    }
    for label in labels:
        column_config_dict[label] = st.column_config.NumberColumn(label, help=f"Count of idle times in {label} range", format="%d", width="small")

    st.dataframe(combined_summary_report, use_container_width=True, hide_index=True, column_config=column_config_dict)

    st.markdown("---")
    st.markdown("#### 🔍 Individual Agent Analysis")
    col1, col2 = st.columns(2)
    with col1:
        agent_selected = st.selectbox("Select Agent for Detailed Analysis", sorted(agent_df['agent_name'].unique()))
    with col2:
        close_selected = st.selectbox("Select Close Type for Detailed Analysis", ['All', 'Direct Close', 'Agent Close'])

    filtered = agent_df[agent_df['agent_name'] == agent_selected]
    if close_selected != 'All':
        filtered = filtered[filtered['Close Type'] == close_selected]
    filtered['Idle Type'] = np.where(filtered['Idle Minutes'] > 180, 'Long Gap (>= 180 min)', 'Normal Idle (< 180 min)')
    filtered['Idle Bucket for Individual'] = pd.cut(filtered['Idle Minutes'], bins=bins, labels=labels, right=True)

    st.markdown("##### 📝 Raw Data (Filtered for Selected Agent)")
    display_cols_for_filtered_df = {
        'ticket_id': 'Ticket ID',
        'time_of_action': 'Time of Action',
        'Idle Minutes': 'Idle Minutes',
        'Idle Type': 'Idle Type',
        'Idle Bucket for Individual': 'Idle Time Bucket',
        'agent_name': 'Agent Name',
        'Close Type': 'Close Type'
    }
    cols_to_show = [col for col in display_cols_for_filtered_df.keys() if col in filtered.columns]
    raw_data_column_config = {
        'ticket_id': st.column_config.TextColumn("Ticket ID", help="Unique identifier for the ticket"),
        'time_of_action': st.column_config.DatetimeColumn("Time of Action", format="YYYY-MM-DD HH:mm:ss"),
        'Idle Minutes': st.column_config.NumberColumn("Idle Minutes", format="%.2f"),
        'Idle Type': st.column_config.TextColumn("Idle Type", help="Categorization of idle time"),
        'Idle Bucket for Individual': st.column_config.TextColumn("Idle Time Bucket"),
        'agent_name': st.column_config.TextColumn("Agent Name"),
        'Close Type': st.column_config.TextColumn("Close Type")
    }
    st.dataframe(filtered[cols_to_show].rename(columns=display_cols_for_filtered_df), use_container_width=True, hide_index=True, column_config=raw_data_column_config)

    st.markdown("##### 📊 Idle Time Series (Selected Agent)")
    fig = px.line(filtered, x='time_of_action', y='Idle Minutes',
                  title=f"Idle Time of Agent: {agent_selected}", markers=True,
                  color='Idle Type', color_discrete_map={'Normal Idle (< 180 min)': 'lightgreen', 'Long Gap (>= 180 min)': 'tomato'})
    fig.update_layout(plot_bgcolor='#262626', paper_bgcolor='#262626', font_color='#FAFAFA',
                      title_font_color='#4CAF50', xaxis_title_font_color='#FAFAFA', yaxis_title_font_color='#FAFAFA',
                      xaxis=dict(gridcolor='#3a3a3a'), yaxis=dict(gridcolor='#3a3a3a'))
    st.plotly_chart(fig, use_container_width=True)

# FLR Analysis
with st.expander("⏱️ FLR (First Last Response) Analysis", expanded=False):
    st.markdown("### 📊 First Last Response Time Series")

    def format_minutes_to_hms(minutes):
        if pd.isna(minutes):
            return "N/A"
        total_seconds = minutes * 60
        hours = int(total_seconds // 3600)
        minutes_remainder = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}:{minutes_remainder:02d}:{seconds:02d}"

    if not data_FLR.empty and all(col in data_FLR.columns for col in ['last_agent_flr', 'agent_name', 'flr_min', 'ticket_id', 'ticket_open_datetime']):
        flr_plot_data = data_FLR.dropna(subset=['ticket_open_datetime', 'flr_min'])
        if flr_plot_data.empty:
            st.warning("No valid data available after dropping rows with missing 'ticket_open_datetime' or 'flr_min'.")
        else:
            if 'agent_selected' in locals() and agent_selected:
                flr_plot_data = flr_plot_data[flr_plot_data['agent_name'] == agent_selected].copy()
                title_text = f"First Last Response (FLR) Time Series for Agent: {agent_selected}"
                st.info(f"Displaying FLR time series for agent: **{agent_selected}**.")
            else:
                flr_plot_data = flr_plot_data.copy()
                title_text = "First Last Response (FLR) Time Series for All Agents"
                st.info("No agent selected. Showing FLR time series for all agents.")

            if not flr_plot_data.empty:
                flr_plot_data['FLR Type'] = np.where(flr_plot_data['flr_min'] > 15, 'Long FLR (> 15 min)', 'Normal FLR (<= 15 min)')
                flr_plot_data = flr_plot_data.sort_values('ticket_open_datetime')
                fig_flr = px.line(flr_plot_data, x='ticket_open_datetime', y='flr_min', title=title_text, markers=True,
                                  color='FLR Type' if 'agent_selected' in locals() and agent_selected else 'agent_name',
                                  color_discrete_map={'Normal FLR (<= 15 min)': 'lightgreen', 'Long FLR (> 15 min)': 'tomato'} if 'agent_selected' in locals() and agent_selected else None)
                fig_flr.update_traces(customdata=flr_plot_data['flr_min'].apply(format_minutes_to_hms),
                                      hovertemplate="<b>Ticket Created On:</b> %{x|%Y-%m-%d %H:%M:%S}<br>" +
                                                    "<b>FLR:</b> %{customdata}<br>" +
                                                    ("<b>Agent:</b> %{customdata[0]}<br>" if not ('agent_selected' in locals() and agent_selected) else "") +
                                                    "<extra></extra>")
                fig_flr.update_layout(plot_bgcolor='#262626', paper_bgcolor='#262626', font_color='#FAFAFA',
                                      title_font_color='#4CAF50', xaxis_title="Ticket Created On", yaxis_title="Agent FLR (Minutes)",
                                      xaxis_title_font_color='#FAFAFA', yaxis_title_font_color='#FAFAFA',
                                      xaxis=dict(gridcolor='#3a3a3a'), yaxis=dict(gridcolor='#3a3a3a'))
                max_flr = flr_plot_data['flr_min'].max()
                if not pd.isna(max_flr):
                    tickvals = np.linspace(0, max_flr, num=10)
                    ticktext = [format_minutes_to_hms(val) for val in tickvals]
                    fig_flr.update_yaxes(tickvals=tickvals, ticktext=ticktext)
                st.plotly_chart(fig_flr, use_container_width=True)
            else:
                st.warning(f"No FLR data available for {'selected agent: ' + agent_selected if ('agent_selected' in locals() and agent_selected) else 'any agents'} with valid ticket open dates.")

            st.markdown("---")
            st.markdown("#### 📝 Raw FLR Data Preview")
            display_cols = ['agent_name', 'ticket_id', 'ticket_open_datetime', 'last_agent_flr', 'flr_min', 'flr_>_15_min']
            rename_cols = {
                'agent_name': 'Agent Name',
                'ticket_id': 'Ticket ID',
                'ticket_open_datetime': 'Ticket Created On',
                'last_agent_flr': 'Last Agent FLR (Original)',
                'flr_min': 'FLR in Minutes',
                'flr_>_15_min': 'FLR > 15 Min Flag'
            }
            st.dataframe(flr_plot_data[display_cols].rename(columns=rename_cols), use_container_width=True, hide_index=True,
                         column_config={
                             'Agent Name': st.column_config.TextColumn("Agent Name"),
                             'Ticket ID': st.column_config.TextColumn("Ticket ID"),
                             'Ticket Created On': st.column_config.DatetimeColumn("Ticket Created On", format="YYYY-MM-DD HH:mm:ss"),
                             'Last Agent FLR (Original)': st.column_config.TextColumn("Last Agent FLR (Original)"),
                             'FLR in Minutes': st.column_config.NumberColumn("FLR in Minutes", format="%.2f"),
                             'FLR > 15 Min Flag': st.column_config.NumberColumn("FLR > 15 Min Flag", format="%d")
                         })
    else:
        st.warning("Please upload a valid FLR file with 'AgentName', 'Last Agent FLR', 'Ticket ID', and 'Ticket Created On' columns.")