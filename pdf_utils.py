from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, LongTable, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import HexColor
from io import BytesIO
import pandas as pd

def generate_pdf_from_dataframe(dataframe: pd.DataFrame, filters: dict = None, page_size=letter) -> BytesIO:
    buffer = BytesIO()
    
    # Store original dataframe for processing and modify a copy for display
    display_df = dataframe.copy() 

    # Logic to handle Zone merging for PDF display
    # We will modify the 'Zone' column in display_df for visual merging
    zone_col_index = display_df.columns.get_loc('Zone') + 1 # +1 because of the serial number column

    # Calculate spans and empty out redundant Zone cells
    spans = []
    current_zone = None
    span_start_row = 1 # Start from 1 because row 0 is header
    
    # Prepare data for PDF, including serial number and handling 'Zone' for merging
    pdf_data_rows = []
    for idx, (_, row) in enumerate(display_df.iterrows(), 1):
        row_list = [str(idx)] + [str(cell) if pd.notna(cell) else "" for cell in row]
        pdf_data_rows.append(row_list)

        # Zone merging logic
        if current_zone is None: # First row of the table
            current_zone = row['Zone']
            span_start_row = idx
        elif row['Zone'] == current_zone and row['Division'] != 'Total': # Same zone, not a total row
            # If the current row's zone is the same as the previous,
            # and it's not a 'Total' row, then mark this 'Zone' cell as empty
            # and prepare for spanning.
            pdf_data_rows[-1][zone_col_index] = "" 
        else: # Zone changed or it's a 'Total' row
            # If the zone changes or it's a 'Total' row, close the previous span
            if idx - span_start_row > 1: # Only create span if it covers more than one row
                spans.append(('SPAN', (zone_col_index, span_start_row), (zone_col_index, idx - 1)))
            current_zone = row['Zone']
            span_start_row = idx
            
    # Close the last span if it exists
    if idx - span_start_row > 0:
        spans.append(('SPAN', (zone_col_index, span_start_row), (zone_col_index, idx)))

    num_cols = len(display_df.columns) + 1 
    if num_cols > 10:
        page_size = landscape(letter)
    
    doc = SimpleDocTemplate(buffer, pagesize=page_size, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    elements = []

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 12
    header_style = styles['Normal']
    header_style.fontSize = 10
    header_style.fontName = 'Helvetica'
    header_style.leading = 12
    subtotal_style = styles['Normal']
    subtotal_style.fontSize = 10
    subtotal_style.fontName = 'Helvetica'
    subtotal_style.leading = 12

    data = []
    # Adding "#" for the serial number column
    headers = [Paragraph("#", header_style)] + [Paragraph(str(col), header_style) for col in display_df.columns]
    data.append(headers)
    
    # Add the prepared PDF data rows
    for row_list in pdf_data_rows:
        row_paragraphs = []
        for i, cell_content in enumerate(row_list):
            style_to_apply = normal_style
            # Check if it's a 'Total' row (assuming 'Division' column is at index 2 if 'Zone' is 1)
            # Adjust index based on your actual data structure in row_list
            if i == 2 and cell_content == 'Total': # Assuming Division is the 2nd data column (index 2 after SN and Zone)
                 style_to_apply = subtotal_style # Or a specific bold style for total
            
            row_paragraphs.append(Paragraph(str(cell_content), style_to_apply))
        data.append(row_paragraphs)

    max_width = page_size[0] - 40
    num_cols = len(display_df.columns) + 1
    sn_width = 30
    remaining_width = max_width - sn_width
    
    # Calculate column widths based on content
    col_char_lengths = [len("#")] + [max(len(str(col)), display_df[col].astype(str).apply(len).max()) for col in display_df.columns]
    col_char_lengths = [l if pd.notna(l) else 10 for l in col_char_lengths] 

    total_chars = sum(col_char_lengths)
    col_widths = [sn_width] + [(char_len / total_chars) * remaining_width for char_len in col_char_lengths[1:]]
    col_widths = [max(20, min(150, width)) for width in col_widths]

    total_width = sum(col_widths)
    if total_width > max_width:
        scale_factor = max_width / total_width
        col_widths = [width * scale_factor for width in col_widths]

    table = LongTable(data, colWidths=col_widths, repeatRows=1)
    
    table_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7AB8F5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Changed header font to bold
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
    ]

    # Add the generated spans to the table styles
    table_styles.extend(spans)

    # Conditional styling for "Total" row or subtotal rows
    for i in range(len(data)):
        # Check if the 'Division' column (index 2 in the PDF data) is "Total"
        if len(data[i]) > 2 and data[i][2].text == "Total": 
            table_styles.append(('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'))
            table_styles.append(('BACKGROUND', (0, i), (-1, i), HexColor('#f0f0f0')))

    table.setStyle(TableStyle(table_styles))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer