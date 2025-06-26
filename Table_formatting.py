import pandas as pd
import numpy as np

def style_dataframe(df, numeric_cols):
    # Ensure numeric_cols is a list and exists in DataFrame
    numeric_cols = [col for col in numeric_cols if col in df.columns]
    
    # Create format dictionary for numeric columns
    format_dict = {col: "{:.2f}" for col in numeric_cols}
    
    # Initialize styler
    styler = df.style
    
    # Apply formatting for numeric columns, replacing NaN with "-"
    styler = styler.format(format_dict, na_rep="-")
    
    # Set general table properties
    styler = styler.set_properties(**{
        'text-align': 'center',
        'border': '1px solid #ddd',
        'padding': '5px'
    })
    
    # Set table styles for headers and cells
    styler = styler.set_table_styles([
        {
            'selector': 'th',
            'props': [
                ('background-color', '#1E90FF'),
                ('color', 'white'),
                ('font-weight', 'normal'),
                ('text-align', 'center'),
                ('border', '1px solid #ddd'),
                ('padding', '5px')
            ]
        },
        {
            'selector': 'td',
            'props': [
                ('background-color', '#f9f9f9'),
                ('border', '1px solid #ddd')
            ]
        }
    ])
    
    # Apply alternating row background color
    styler = styler.set_table_styles([
        {
            'selector': 'tr:nth-child(even) td',
            'props': [('background-color', '#ffffff')]
        }
    ], overwrite=False)
    
    # Apply background gradient to numeric columns
    for col in numeric_cols:
        styler = styler.background_gradient(
            cmap='Blues',
            subset=col,
            vmin=df[col].min(),
            vmax=df[col].max()
        )
    
    # Define function to highlight subtotal rows
    def highlight_subtotal(row):
        # Check if the row is a subtotal (e.g., contains "Total" in the first column or has NaN/empty values)
        first_col = df.columns[0]
        is_subtotal = (
            str(row[first_col]).strip().lower() == "total" or
            pd.isna(row[first_col]) or
            row[first_col] == ""
        )
        return ['font-weight: bold; background-color: #f0f0f0' if is_subtotal else '' for _ in row]
    
    # Apply subtotal highlighting
    styler = styler.apply(highlight_subtotal, axis=1)
    
    return styler