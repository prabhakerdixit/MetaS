from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, LongTable, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import HexColor
from io import BytesIO
import pandas as pd

def generate_pdf_from_dataframe(dataframe: pd.DataFrame, filters: dict = None, page_size=letter, header_text: str = None) -> BytesIO:
    buffer = BytesIO()
    
    display_df = dataframe.copy() 

    try:
        zone_col_index_df = display_df.columns.get_loc('Zone')
        zone_col_index_pdf = zone_col_index_df + 1
    except KeyError:
        zone_col_index_pdf = -1

    spans = []
    current_zone = None
    span_start_row = 1
    
    pdf_data_rows = []
    for idx, (_, row) in enumerate(display_df.iterrows(), 1):
        row_list = [str(idx)] + [str(cell) if pd.notna(cell) else "" for cell in row]
        pdf_data_rows.append(row_list)

        if zone_col_index_pdf != -1:
            if current_zone is None:
                current_zone = row['Zone']
                span_start_row = idx
            elif row['Zone'] == current_zone and row.get('Division Name') != 'Total':
                pdf_data_rows[-1][zone_col_index_pdf] = "" 
            else:
                if idx - span_start_row > 1:
                    spans.append(('SPAN', (zone_col_index_pdf, span_start_row), (zone_col_index_pdf, idx - 1)))
                current_zone = row['Zone']
                span_start_row = idx
                
    if zone_col_index_pdf != -1 and len(display_df) > 0 and (idx - span_start_row > 0):
        spans.append(('SPAN', (zone_col_index_pdf, span_start_row), (zone_col_index_pdf, idx)))

    num_cols_df = len(display_df.columns)
    if num_cols_df + 1 > 10:
        page_size = landscape(letter)
    
    doc = SimpleDocTemplate(buffer, pagesize=page_size, leftMargin=20, rightMargin=20, topMargin=40, bottomMargin=20)
    elements = []

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 12
    header_style = styles['Normal']
    header_style.fontSize = 12
    header_style.fontName = 'Helvetica-Bold' # This correctly makes the Paragraph bold
    header_style.leading = 13
    subtotal_style = styles['Normal']
    subtotal_style.fontSize = 12
    subtotal_style.fontName = 'Helvetica'
    subtotal_style.leading = 12

    if header_text:
        title_style = styles['h2']
        title_style.alignment = 1
        title_style.spaceAfter = 2
        elements.append(Paragraph(header_text, title_style))
        elements.append(Spacer(1, 0.02 * doc.height))

    data = []
    headers = [Paragraph("#", header_style)] + [Paragraph(str(col), header_style) for col in display_df.columns]
    data.append(headers)
    
    for row_list in pdf_data_rows:
        row_paragraphs = []
        for i, cell_content in enumerate(row_list):
            style_to_apply = normal_style
            try:
                division_name_col_idx_df = display_df.columns.get_loc('Division Name')
                division_name_col_idx_pdf = division_name_col_idx_df + 1
                if i == division_name_col_idx_pdf and cell_content == 'Total':
                    style_to_apply = subtotal_style
            except KeyError:
                pass

            row_paragraphs.append(Paragraph(str(cell_content), style_to_apply))
        data.append(row_paragraphs)

    max_width = page_size[0] - 40
    
    col_char_lengths = [len("#")] + [max(len(str(col)), display_df[col].astype(str).apply(len).max() if not display_df[col].empty else 10) for col in display_df.columns]
    col_char_lengths = [l if pd.notna(l) else 10 for l in col_char_lengths]

    total_chars = sum(col_char_lengths)
    
    sn_width_fixed = 30 
    
    remaining_width = max_width - sn_width_fixed
    
    col_widths = [sn_width_fixed]
    if total_chars - col_char_lengths[0] > 0:
        col_widths.extend([(char_len / (total_chars - col_char_lengths[0])) * remaining_width for char_len in col_char_lengths[1:]])
    else:
        col_widths.extend([remaining_width / num_cols_df] * num_cols_df)

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
        ('FONTSIZE', (0, 0), (-1, 0), 12), # Changed from 10 to 12 for consistent header font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
    ]

    table_styles.extend(spans)

    try:
        division_name_col_idx_pdf_data = display_df.columns.get_loc('Division Name') + 1
        for i in range(len(data)):
            if len(data[i]) > division_name_col_idx_pdf_data and data[i][division_name_col_idx_pdf_data].text == "Total": 
                table_styles.append(('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'))
                table_styles.append(('BACKGROUND', (0, i), (-1, i), HexColor('#f0f0f0')))
    except KeyError:
        pass

    table.setStyle(TableStyle(table_styles))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer
