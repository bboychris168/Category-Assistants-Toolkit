import streamlit as st
import pandas as pd
from rapidfuzz import fuzz, process
import re
import io

st.set_page_config(page_title="Price Impact Item Code Matcher", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .section { background: var(--section-bg-color); border: 1px solid var(--section-border-color); border-radius: 8px; padding: 1rem; margin: 1rem 0; }
    .card { background: var(--card-bg-color); border: 1px solid var(--card-border-color); border-radius: 6px; padding: 1rem; margin: 0.5rem 0; }
    h1, h2, h3 { color: var(--text-color); margin-bottom: 0.5rem; }
    p { color: var(--text-color); margin: 0.5rem 0; }
    [data-theme="light"] {
        --section-bg-color: #ffffff;
        --section-border-color: #e0e0e0;
        --card-bg-color: #f8f9fa;
        --card-border-color: #e0e0e0;
        --text-color: #2C3E50;
    }
    [data-theme="dark"] {
        --section-bg-color: #1E1E1E;
        --section-border-color: #404040;
        --card-bg-color: #262730;
        --card-border-color: #404040;
        --text-color: #E0E0E0;
    }
    .dataframe { border: none !important; background: var(--card-bg-color) !important; }
    .dataframe th { background-color: var(--section-bg-color) !important; }
    .dataframe td, .dataframe th { color: var(--text-color) !important; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""<div class="section"><h1>📊 Price Impact Item Code Matcher</h1>
<div class="card"><p>Match your system's item codes with supplier codes using intelligent fuzzy matching.</p></div></div>""", unsafe_allow_html=True)

# Quick Guide
st.markdown("""<div class="section"><h2>🚀 Quick Guide</h2><div class="card">
1. Upload supplier's Excel file (with item codes and prices)<br>
2. Upload your system's data file (with internal codes)<br>
3. Select matching columns<br>
4. Review results and download CSV</div></div>""", unsafe_allow_html=True)

# File Upload
col1, col2 = st.columns(2)
with col1:
    st.markdown("""<div class="card"><h3>📈 Supplier's File</h3></div>""", unsafe_allow_html=True)
    supplier_file = st.file_uploader("Upload supplier's Excel file", type=['xlsx', 'xls'])
    if supplier_file:
        st.success(f"✅ {supplier_file.name}")

with col2:
    st.markdown("""<div class="card"><h3>🗄️ System's Data</h3></div>""", unsafe_allow_html=True)
    system_file = st.file_uploader("Upload your system's data file", type=['xlsx', 'xls', 'csv'])
    if system_file:
        st.success(f"✅ {system_file.name}")

def normalize_code(code):
    # Convert to string and lowercase
    code = str(code).lower().strip()
    # Remove any special characters and spaces
    code_clean = re.sub(r'[^\w]', '', code)
    return code_clean

def get_best_match_score(str1, str2):
    # Get cleaned versions of the codes
    code1 = normalize_code(str1)
    code2 = normalize_code(str2)
    
    # If exact match after normalization, return 100
    if code1 == code2:
        return 100.0
    
    # Get lengths of both codes
    len1 = len(code1)
    len2 = len(code2)
    
    # Calculate length difference percentage
    length_diff_pct = abs(len1 - len2) / max(len1, len2)
    
    # If length difference is more than 30%, return 0
    if length_diff_pct > 0.3:
        return 0.0
    
    # Calculate base similarity score
    ratio_score = fuzz.ratio(code1, code2)
    
    # More aggressive length penalty
    length_penalty = (1 - length_diff_pct) * 0.5
    
    # If the base score is too low, return 0
    if ratio_score < 60:
        return 0.0
    
    # Calculate final score with length penalty
    final_score = ratio_score * (0.5 + length_penalty)
    
    # Cap non-exact matches at 95%
    return min(final_score, 95.0)

# Process files when both are uploaded
if supplier_file and system_file:
    try:
        supplier_df = pd.read_excel(supplier_file)
        system_df = pd.read_csv(system_file, encoding='utf-8') if system_file.name.endswith('.csv') else pd.read_excel(system_file)

        # Clean up any potential encoding issues in the data
        for col in supplier_df.columns:
            if supplier_df[col].dtype == 'object':
                supplier_df[col] = supplier_df[col].apply(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if pd.notnull(x) else x)
        
        for col in system_df.columns:
            if system_df[col].dtype == 'object':
                system_df[col] = system_df[col].apply(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if pd.notnull(x) else x)

        st.markdown("""<div class="section"><h2>⚙️ Configure</h2></div>""", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            supplier_item_col = st.selectbox("Supplier's item code column", supplier_df.columns.tolist())
            supplier_price_col = st.selectbox("Supplier's price column", supplier_df.columns.tolist())

        with col2:
            system_item_col = st.selectbox("System's item code column", system_df.columns.tolist())

        if st.button("Start Matching", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            total_items = len(system_df)

            for idx, system_row in system_df.iterrows():
                system_code = str(system_row[system_item_col])
                best_match = best_price = None
                best_score = 0
                
                progress = (idx + 1) / total_items
                progress_bar.progress(progress)
                status_text.text(f"Processing {idx + 1}/{total_items}")

                for _, supplier_row in supplier_df.iterrows():
                    supplier_code = str(supplier_row[supplier_item_col])
                    score = get_best_match_score(system_code, supplier_code)
                    if score > best_score:
                        best_score = score
                        best_match = supplier_code
                        best_price = supplier_row[supplier_price_col]

                results.append({
                    'System Code': system_code,
                    'Supplier Code': best_match,
                    'Match Score': best_score,
                    'Cost Price': best_price
                })

            progress_bar.empty()
            status_text.empty()

            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('Match Score', ascending=False)
            results_df['Match Score'] = results_df['Match Score'].astype(float).round(1).astype(str) + '%'
            results_df['Cost Price'] = '$' + results_df['Cost Price'].astype(float).round(2).astype(str)

            st.markdown("""<div class="section"><h2>📊 Results</h2></div>""", unsafe_allow_html=True)
            
            # Match quality metrics
            high_matches = len(results_df[results_df['Match Score'].str.rstrip('%').astype(float) >= 90])
            medium_matches = len(results_df[results_df['Match Score'].str.rstrip('%').astype(float).between(70, 89)])
            low_matches = len(results_df[results_df['Match Score'].str.rstrip('%').astype(float) < 70])

            col1, col2, col3 = st.columns(3)
            col1.metric("High Matches (90%+)", high_matches)
            col2.metric("Medium Matches (70-89%)", medium_matches)
            col3.metric("Low Matches (<70%)", low_matches)

            st.dataframe(results_df, height=400, use_container_width=True)
            
            # Clean the results DataFrame for any remaining encoding issues
            for col in results_df.columns:
                if results_df[col].dtype == 'object':
                    results_df[col] = results_df[col].apply(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if pd.notnull(x) else x)
            
            # Export to CSV with UTF-8 encoding
            csv_buffer = io.StringIO()
            results_df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_str = csv_buffer.getvalue()
            
            st.download_button("📥 Download CSV", csv_str, "matching_results.csv", "text/csv", encoding='utf-8')

    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("Please upload both files to begin matching")
