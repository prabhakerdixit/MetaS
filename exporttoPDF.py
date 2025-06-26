from fpdf import FPDF
from datetime import date

def export_to_pdf(df_to_export):
    """
    Generates a PDF report from the Social_Media_summary DataFrame.
    
    This function processes the DataFrame to create the summary table,
    sorts it, excludes rows with zero cases, and then generates a PDF
    with merged cells for the 'Zone' column.
    """
    # 1. Prepare the data for the PDF report
    social_media_summary = (
        df_to_export.groupby(['Zone', 'Division'], dropna=False)
        .agg({
            'IsSocialMedia': 'sum',
            'MoreThan90Min_SM': 'sum'
        })
        .rename(columns={
            'IsSocialMedia': 'Total Cases',
            'MoreThan90Min_SM': '>90 Min Cases'
        })
        .reset_index()
    )

    # 2. Filter and sort the data
    # Exclude rows where Total Cases is 0
    social_media_summary = social_media_summary[social_media_summary['Total Cases'] > 0]
    
    # Sort by 'Zone' and then by '>90 Min Cases' largest to smallest
    social_media_summary.sort_values(by=['Zone', '>90 Min Cases'], ascending=[True, False], inplace=True)
    
    # 3. Create the PDF document
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Set up fonts and colors
    pdf.set_font("Arial", size=16, style='B')
    pdf.set_fill_color(200, 220, 255) # Light blue background for header

    # Add title and date
    pdf.cell(0, 10, 'Social Media Performance Report', 0, 1, 'C', 1)
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"Report Date: {date.today().strftime('%Y-%m-%d')}", 0, 1, 'R')
    pdf.ln(5)

    # 4. Create the table with merged Zone cells
    pdf.set_font("Arial", size=10, style='B')
    col_widths = [40, 50, 40, 40]  # Zone, Division, Cases, >90 Min Cases
    col_names = ['Zone', 'Division', 'Total Cases', '>90 Min Cases']
    
    # Draw table headers
    pdf.set_fill_color(220, 220, 220)
    for col in col_names:
        pdf.cell(col_widths[col_names.index(col)], 10, col, 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    
    # Get the unique zones to group them
    unique_zones = social_media_summary['Zone'].unique()
    
    for zone in unique_zones:
        zone_df = social_media_summary[social_media_summary['Zone'] == zone]
        num_rows_in_zone = len(zone_df)
        
        # Capture the starting Y position for the zone's rows
        start_y_for_zone = pdf.get_y()

        # Draw the rows for the current zone
        for index, row in zone_df.iterrows():
            # Add a placeholder for the Zone column
            pdf.cell(col_widths[0], 10, '', 0, 0, 'C') 

            # Draw the other columns
            pdf.set_fill_color(255, 255, 255)
            pdf.cell(col_widths[1], 10, str(row['Division']), 1, 0, 'C', 1)
            pdf.cell(col_widths[2], 10, str(row['Total Cases']), 1, 0, 'C', 1)
            pdf.cell(col_widths[3], 10, str(row['>90 Min Cases']), 1, 1, 'C', 1)
            
        # After drawing all rows for the zone, draw the merged cell
        end_y_for_zone = pdf.get_y()
        
        # Go back to the starting position of the zone group
        pdf.set_xy(10, start_y_for_zone)
        
        # Draw the merged cell
        pdf.set_font("Arial", size=10, style='B')
        pdf.set_fill_color(240, 240, 240)
        pdf.multi_cell(col_widths[0], end_y_for_zone - start_y_for_zone, str(zone), 1, 'C', 1)
        
        # Move the cursor back to the end of the last row
        pdf.set_xy(10, end_y_for_zone)

    # Output the PDF as bytes
    return pdf.output(dest='S').encode('latin-1')