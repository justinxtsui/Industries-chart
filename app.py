import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from collections import Counter
import io
from datetime import datetime

st.title('Top Industries/Buzzwords Chart')

st.write('Upload a CSV file with columns for Industries and Buzzwords.')

uploaded_file = st.file_uploader('Choose a CSV file', type=['csv'])

if uploaded_file is not None:
    company_df = pd.read_csv(uploaded_file)
    
    # Auto-detect column names (handle both formats)
    industries_col = None
    buzzwords_col = None
    amount_col = None
    
    if 'Industries' in company_df.columns:
        industries_col = 'Industries'
    elif '(Company) Industries' in company_df.columns:
        industries_col = '(Company) Industries'
    
    if 'Buzzwords' in company_df.columns:
        buzzwords_col = 'Buzzwords'
    elif '(Company) Buzzwords' in company_df.columns:
        buzzwords_col = '(Company) Buzzwords'
    
    # Check for amount raised column
    if 'Amount raised (converted to GBP)' in company_df.columns:
        amount_col = 'Amount raised (converted to GBP)'
    
    if industries_col is None or buzzwords_col is None:
        st.error("CSV must contain columns: 'Industries' and 'Buzzwords' OR '(Company) Industries' and '(Company) Buzzwords'.")
    else:
        # Ranking option
        ranking_by = st.radio('Rank by:', ['Count', 'Total Amount Raised'])
        
        # Build industry/buzzword data with counts and amounts
        industry_data = {}
        for i, row in company_df.iterrows():
            inds = str(row[industries_col]).split(',') if pd.notna(row[industries_col]) else []
            buzz = str(row[buzzwords_col]).split(',') if pd.notna(row[buzzwords_col]) else []
            all_items = [item.strip() for item in inds + buzz if item.strip()]
            
            amount = row[amount_col] if amount_col and pd.notna(row[amount_col]) else 0
            
            for item in all_items:
                if item not in industry_data:
                    industry_data[item] = {'count': 0, 'total_amount': 0}
                industry_data[item]['count'] += 1
                industry_data[item]['total_amount'] += amount
        
        # Get all unique industries sorted by selected metric
        if ranking_by == 'Count':
            all_industries = sorted(industry_data.keys(), key=lambda x: industry_data[x]['count'], reverse=True)
        else:
            all_industries = sorted(industry_data.keys(), key=lambda x: industry_data[x]['total_amount'], reverse=True)
        
        # Exclusion multiselect
        excluded_industries = st.multiselect(
            'Exclude specific industries/buzzwords:',
            options=all_industries,
            default=[]
        )
        
        # Filter out excluded industries
        filtered_data = {k: v for k, v in industry_data.items() if k not in excluded_industries}
        
        # Number input for top N
        max_available = len(filtered_data)
        top_n = st.number_input(
            'Number of top industries/buzzwords to display:',
            min_value=1,
            max_value=max_available,
            value=min(10, max_available)
        )
        
        # Get top N from filtered data
        if ranking_by == 'Count':
            topN = sorted(filtered_data.items(), key=lambda x: x[1]['count'], reverse=True)[:top_n]
            labels = [k for k, v in topN]
            values = [v['count'] for k, v in topN]
        else:
            topN = sorted(filtered_data.items(), key=lambda x: x[1]['total_amount'], reverse=True)[:top_n]
            labels = [k for k, v in topN]
            values = [v['total_amount'] for k, v in topN]

        chart_title = st.text_input('Chart title:', value=f'Top {top_n} Industries/Buzzwords by {ranking_by}')

        # Function to format values to 3 significant figures
        def format_value(value, is_amount=False):
            if is_amount:
                if value == 0:
                    return '£0'
                if value >= 1_000_000_000:
                    formatted = value / 1_000_000_000
                    if formatted >= 100: return f'£{formatted:.0f}b'
                    elif formatted >= 10: return f'£{formatted:.1f}b'
                    else: return f'£{formatted:.2f}b'
                elif value >= 1_000_000:
                    formatted = value / 1_000_000
                    if formatted >= 100: return f'£{formatted:.0f}m'
                    elif formatted >= 10: return f'£{formatted:.1f}m'
                    else: return f'£{formatted:.2f}m'
                elif value >= 1_000:
                    formatted = value / 1_000
                    if formatted >= 100: return f'£{formatted:.0f}k'
                    elif formatted >= 10: return f'£{formatted:.1f}k'
                    else: return f'£{formatted:.2f}k'
                else:
                    if value >= 100: return f'£{value:.0f}'
                    elif value >= 10: return f'£{value:.1f}'
                    else: return f'£{value:.2f}'
            else:
                return f'{int(value):,}'

        mpl.rcParams['svg.fonttype'] = 'none'
        mpl.rcParams['pdf.fonttype'] = 42
        mpl.rcParams['font.family'] = 'Public Sans'
        mpl.rcParams['font.sans-serif'] = ['Public Sans', 'Arial', 'DejaVu Sans']
        mpl.rcParams['font.weight'] = 'normal'

        y_pos = list(range(len(labels)))
        fig, ax = plt.subplots(figsize=(10, 6))
        max_value = max(values)

        ax.barh(y_pos, [max_value] * len(values), color='#E0E0E0', alpha=1.0, height=0.8)
        for i, (y, value) in enumerate(zip(y_pos, values)):
            color = '#4B4897' if i == 0 else '#A4A2F2'
            ax.barh(y, value, color=color, height=0.8)

        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.xaxis.set_visible(False)
        ax.tick_params(axis='y', which='both', length=0)

        offset_points = 5.67
        offset_data = offset_points * (max_value / (ax.get_window_extent().width * 72 / fig.dpi))
        for i, (label, value) in enumerate(zip(labels, values)):
            text_color = 'white' if i == 0 else 'black'
            ax.text(offset_data, y_pos[i], label,
                    fontsize=13, ha='left', va='center', fontweight='normal', color=text_color)
            ax.text(max_value - offset_data, y_pos[i], format_value(value, is_amount=(ranking_by == 'Total Amount Raised')),
                    fontsize=13, ha='right', va='center', fontweight='semibold', color=text_color)

        ax.set_title(chart_title, fontsize=15, pad=20, fontweight='normal')
        ax.invert_yaxis()
        plt.tight_layout()
        st.pyplot(fig)

        # Download as SVG
        svg_buffer = io.BytesIO()
        fig.savefig(svg_buffer, format='svg', bbox_inches='tight')
        svg_buffer.seek(0)
        st.download_button(
            label='Download Chart as SVG',
            data=svg_buffer,
            file_name=f'{chart_title.replace(" ", "_").lower()}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.svg',
            mime='image/svg+xml'
        )
