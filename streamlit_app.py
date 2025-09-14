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
    
    # First try to match the base code (before any slash)
    base_code = code.split('/')[0]
    base_code_clean = re.sub(r'[^\w]', '', base_code)
    
    # Store the suffix if it exists
    suffix = code.split('/')[1] if '/' in code else ''
    suffix_clean = re.sub(r'[^\w]', '', suffix) if suffix else ''
    
    # Return both cleaned versions for comparison
    return base_code_clean, suffix_clean

def get_best_match_score(str1, str2):
    # Get cleaned versions of the codes
    code1_base, code1_suffix = normalize_code(str1)
    code2_base, code2_suffix = normalize_code(str2)
    
    # If exact match after normalization, return 100
    if code1_base + code1_suffix == code2_base + code2_suffix:
        return 100.0
    
    # If base codes match exactly
    if code1_base == code2_base:
        # If one has no suffix and other does, give high score but not 100
        if not code1_suffix or not code2_suffix:
            return 90.0
        
        # If both have suffixes, compare them
        suffix_score = fuzz.ratio(code1_suffix, code2_suffix)
        return 85.0 + (suffix_score * 0.15)  # Max 100, Min 85
    
    # Calculate base similarity score
    base_score = fuzz.ratio(code1_base, code2_base)
    
    # If base score is too low, return 0
    if base_score < 60:
        return 0.0
    
    # Calculate final score
    final_score = base_score * 0.8  # Give more weight to base code match
    
    return min(final_score, 95.0)

# Process files when both are uploaded
if supplier_file and system_file:
    try:
        supplier_df = pd.read_excel(supplier_file)
        system_df = pd.read_csv(system_file, encoding='utf-8') if system_file.name.endswith('.csv') else pd.read_excel(system_file)

        # Clean up any potential encoding issues
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

            # New UI controls for threshold / top-N
            threshold = st.sidebar.slider("Match threshold (%)", min_value=0, max_value=100, value=70, step=1)
            top_n = st.sidebar.number_input("Top N matches to show", min_value=1, max_value=5, value=1, step=1)

            total_items = len(system_df)

            # Precompute normalized supplier keys to speed matching
            supplier_rows = []
            supplier_full_keys = []
            for _, supplier_row in supplier_df.iterrows():
                supplier_code = str(supplier_row[supplier_item_col])
                base, suffix = normalize_code(supplier_code)
                full_key = base + suffix  # compact normalized token
                supplier_full_keys.append(full_key)
                supplier_rows.append({
                    'orig_code': supplier_code,
                    'full_key': full_key,
                    'base': base,
                    'suffix': suffix,
                    'price': supplier_row[supplier_price_col]
                })

            # Iterate system rows and use rapidfuzz.process to find matches
            for idx, system_row in system_df.iterrows():
                system_code = str(system_row[system_item_col])
                sys_base, sys_suffix = normalize_code(system_code)
                sys_full = sys_base + sys_suffix

                progress = (idx + 1) / total_items
                progress_bar.progress(progress)
                status_text.text(f"Processing {idx + 1}/{total_items}")

                # Quick exact match check on normalized full key
                best_match = None
                best_score = 0
                best_price = None
                top_matches_list = []

                # Use rapidfuzz to get top candidates quickly
                matches = process.extract(sys_full, supplier_full_keys, scorer=fuzz.ratio, limit=top_n)
                # matches are tuples (matched_key, score, index)
                for matched_key, score, match_idx in matches:
                    supplier_info = supplier_rows[match_idx]
                    # Convert to a stable score using existing business logic
                    calc_score = get_best_match_score(system_code, supplier_info['orig_code'])
                    top_matches_list.append({
                        'Supplier Code': supplier_info['orig_code'],
                        'Score': round(calc_score, 1),
                        'Price': supplier_info['price']
                    })
                    if calc_score > best_score:
                        best_score = calc_score
                        best_match = supplier_info['orig_code']
                        best_price = supplier_info['price']

                # Apply threshold filter (store even below threshold but mark low)
                results.append({
                    'System Code': system_code,
                    'Supplier Code': best_match,
                    'Match Score': round(best_score, 1),
                    'Cost Price': best_price,
                    'Top Matches': "; ".join([f"{m['Supplier Code']} ({m['Score']}%)" for m in top_matches_list])
                })

            progress_bar.empty()
            status_text.empty()

            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('Match Score', ascending=False)

            # Safe numeric/currency handling for Cost Price
            results_df['Cost Price Numeric'] = pd.to_numeric(results_df['Cost Price'], errors='coerce')
            results_df['Cost Price Display'] = results_df['Cost Price Numeric'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")

            # Keep numeric Match Score column for filtering/metrics; create display version
            results_df['Match Score Display'] = results_df['Match Score'].apply(lambda x: f"{x:.1f}%")

            st.markdown("""<div class="section"><h2>📊 Results</h2></div>""", unsafe_allow_html=True)
            
            # Match quality metrics (use numeric scores)
            high_matches = len(results_df[results_df['Match Score'] >= 90])
            medium_matches = len(results_df[results_df['Match Score'].between(70, 89)])
            low_matches = len(results_df[results_df['Match Score'] < 70])

            col1, col2, col3 = st.columns(3)
            col1.metric("High Matches (90%+)", high_matches)
            col2.metric("Medium Matches (70-89%)", medium_matches)
            col3.metric("Low Matches (<70%)", low_matches)

            # Apply threshold filter for display
            filtered_df = results_df[results_df['Match Score'] >= threshold].copy()

            # Display columns and nicer labels
            display_df = filtered_df[['System Code', 'Supplier Code', 'Match Score Display', 'Cost Price Display', 'Top Matches']].rename(columns={
                'Match Score Display': 'Match Score',
                'Cost Price Display': 'Cost Price'
            })

            st.dataframe(display_df, height=400, use_container_width=True)
            
            # Clean the results DataFrame for any remaining encoding issues
            for col in display_df.columns:
                if display_df[col].dtype == 'object':
                    display_df[col] = display_df[col].apply(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if pd.notnull(x) else x)
            
            # Export to CSV with UTF-8 encoding (use numeric score and numeric price too)
            export_df = filtered_df.copy()
            export_df = export_df.rename(columns={'Match Score': 'Match Score (%)', 'Cost Price Numeric': 'Cost Price'})
            csv_buffer = io.StringIO()
            export_df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_str = csv_buffer.getvalue()
            
            st.download_button("📥 Download CSV", csv_str, "matching_results.csv", "text/csv")
    except Exception as e:
        st.error(f"Error processing files: {e}")
        st.exception(e)
else:
    st.info("Please upload both files to begin matching")
