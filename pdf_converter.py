from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, LongTable, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import HexColor
from io import BytesIO
import pandas as pd
import numpy as np

def pdf_generator(dataframe: pd.DataFrame, header_text: str = None) -> BytesIO:
    """
    Generates a PDF from a pandas DataFrame, including a header and handling "Total" rows.

    Args:
        dataframe (pd.DataFrame): The DataFrame to convert to PDF.
        header_text (str, optional): Text to display as a header at the top of the PDF. Defaults to None.

    Returns:
        BytesIO: A BytesIO object containing the generated PDF.
    """
    buffer = BytesIO()

    # Handle empty dataframe case
    if dataframe.empty:
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=20, rightMargin=20, topMargin=40, bottomMargin=20)
        elements = []
        styles = getSampleStyleSheet()
        
        if header_text:
            title_style = styles['h2']
            title_style.alignment = 1
            title_style.spaceAfter = 12
            elements.append(Paragraph(header_text, title_style))
            elements.append(Spacer(1, 0.2 * doc.height))

        no_data_style = styles['Normal']
        no_data_style.alignment = 1
        no_data_style.fontSize = 14
        elements.append(Paragraph("No data to display for the selected filters.", no_data_style))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # Determine page size based on number of columns
    num_cols = len(dataframe.columns) + 1  # +1 for the serial number column
    page_size = landscape(letter) if num_cols > 10 else letter
    
    doc = SimpleDocTemplate(buffer, pagesize=page_size, leftMargin=20, rightMargin=20, topMargin=40, bottomMargin=20)
    elements = []

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 10
    header_style = styles['Normal']
    header_style.fontSize = 10
    header_style.fontName = 'Helvetica-Bold'
    header_style.leading = 10
    subtotal_style = styles['Normal']
    subtotal_style.fontSize = 10
    subtotal_style.fontName = 'Helvetica' # Make subtotal rows bold
    subtotal_style.leading = 10

    if header_text:
        title_style = styles['h2']
        title_style.alignment = 1
        title_style.spaceAfter = 2
        elements.append(Paragraph(header_text, title_style))
        elements.append(Spacer(1, 0.02 * doc.height))

    data = []
    # Prepare header row with serial number
    headers = [Paragraph("#", header_style)] + [Paragraph(str(col), header_style) for col in dataframe.columns]
    data.append(headers)

    # Convert DataFrame rows to list of lists, handling Paragraph for each cell
    for idx, (_, row) in enumerate(dataframe.iterrows(), 1):
        # Check if it's a "Total" row. We need to be careful with column types here.
        # Check if the first non-serial column (index 0 in 'row' Series, index 1 in 'data' list) is "Total"
        # Or if it's the second column ('Division Name' or 'Type' or 'Sub Type') that is "Total"
        is_total_row = False
        if dataframe.columns[0] in ['Zone', 'Type', 'Sub Type']: # For cases where the first column is the group
            if str(row[dataframe.columns[0]]).strip() == 'Total':
                is_total_row = True
        elif len(dataframe.columns) > 1 and dataframe.columns[1] == 'Division Name': # For Zone/Division summary
            if str(row['Division Name']).strip() == 'Total':
                is_total_row = True
        
        style = subtotal_style if is_total_row else normal_style
        
        # Prepend serial number as Paragraph
        row_data = [Paragraph(str(idx), style)] + [Paragraph(str(cell) if pd.notna(cell) else "", style) for cell in row]
        data.append(row_data)

    max_width = page_size[0] - 40
    sn_width = 30
    remaining_width = max_width - sn_width
    
    # Calculate column widths based on content
    col_char_lengths = [len("#")] + [max(len(str(col)), dataframe[col].astype(str).apply(len).max() if not dataframe[col].empty else 10) for col in dataframe.columns]
    col_char_lengths = [l if pd.notna(l) else 10 for l in col_char_lengths]

    total_chars = sum(col_char_lengths)
    
    col_widths = [sn_width]
    if total_chars - col_char_lengths[0] > 0:
        col_widths.extend([(char_len / (total_chars - col_char_lengths[0])) * remaining_width for char_len in col_char_lengths[1:]])
    else:
        col_widths.extend([remaining_width / (num_cols - 1)] * (num_cols - 1)) # Distribute equally if no content chars

    col_widths = [max(20, min(200, width)) for width in col_widths]

    total_width_after_constrain = sum(col_widths)
    if total_width_after_constrain > max_width:
        scale_factor = max_width / total_width_after_constrain
        col_widths = [width * scale_factor for width in col_widths]

    table = LongTable(data, colWidths=col_widths, repeatRows=1)
    
    table_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7AB8F5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
    ]

    # Conditional styling for "Total" row or subtotal rows within the TableStyle
    for i in range(1, len(data)): # Start from 1 to skip header row
        # Attempt to get the cell content that might contain "Total"
        # This assumes "Total" would be in one of the first few data columns
        first_data_col_content = str(data[i][1].text).strip() if len(data[i]) > 1 else ""
        second_data_col_content = str(data[i][2].text).strip() if len(data[i]) > 2 else ""

        if first_data_col_content == "Total" or second_data_col_content == "Total":
            table_styles.append(('FONTNAME', (0, i), (-1, i), 'Helvetica'))
            table_styles.append(('BACKGROUND', (0, i), (-1, i), HexColor('#f0f0f0')))
            
    table.setStyle(TableStyle(table_styles))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer
