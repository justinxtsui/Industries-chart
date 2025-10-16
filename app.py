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
    if 'Industries' not in company_df or 'Buzzwords' not in company_df:
        st.error("CSV must contain columns: 'Industries' and 'Buzzwords'.")
    else:
        industry_list = []
        for i, row in company_df.iterrows():
            inds = str(row['Industries']).split(',') if pd.notna(row['Industries']) else []
            buzz = str(row['Buzzwords']).split(',') if pd.notna(row['Buzzwords']) else []
            industry_list.extend([item.strip() for item in inds + buzz if item.strip()])

        industry_counter = Counter(industry_list)
        
        # Get all unique industries sorted by count
        all_industries = [k for k, v in industry_counter.most_common()]
        
        # Exclusion multiselect
        excluded_industries = st.multiselect(
            'Exclude specific industries/buzzwords:',
            options=all_industries,
            default=[]
        )
        
        # Filter out excluded industries
        filtered_counter = {k: v for k, v in industry_counter.items() if k not in excluded_industries}
        
        # Number input for top N
        max_available = len(filtered_counter)
        top_n = st.number_input(
            'Number of top industries/buzzwords to display:',
            min_value=1,
            max_value=max_available,
            value=min(10, max_available)
        )
        
        # Get top N from filtered data
        topN = Counter(filtered_counter).most_common(top_n)
        labels = [k for k, v in topN]
        counts = [v for k, v in topN]

        chart_title = st.text_input('Chart title:', value=f'Top {top_n} Industries/Buzzwords')

        mpl.rcParams['svg.fonttype'] = 'none'
        mpl.rcParams['pdf.fonttype'] = 42
        mpl.rcParams['font.family'] = 'Public Sans'
        mpl.rcParams['font.sans-serif'] = ['Public Sans', 'Arial', 'DejaVu Sans']
        mpl.rcParams['font.weight'] = 'normal'

        y_pos = list(range(len(labels)))
        fig, ax = plt.subplots(figsize=(10, 6))
        max_count = max(counts)

        ax.barh(y_pos, [max_count] * len(counts), color='#E0E0E0', alpha=1.0, height=0.8)
        for i, (y, count) in enumerate(zip(y_pos, counts)):
            color = '#4B4897' if i == 0 else '#A4A2F2'
            ax.barh(y, count, color=color, height=0.8)

        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.xaxis.set_visible(False)
        ax.tick_params(axis='y', which='both', length=0)

        offset_points = 5.67
        offset_data = offset_points * (max_count / (ax.get_window_extent().width * 72 / fig.dpi))
        for i, (label, count) in enumerate(zip(labels, counts)):
            text_color = 'white' if i == 0 else 'black'
            ax.text(offset_data, y_pos[i], label,
                    fontsize=13, ha='left', va='center', fontweight='normal', color=text_color)
            ax.text(max_count - offset_data, y_pos[i], f'{count:,}',
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
