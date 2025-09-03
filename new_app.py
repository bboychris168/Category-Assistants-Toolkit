import streamlit as st
import pandas as pd
from rapidfuzz import fuzz, process
import re
import io

# Set page config
st.set_page_config(
    page_title="Item Code Matcher",
    page_icon="🔍",
    layout="wide"
)

# Define the CSS for both light and dark modes
st.markdown("""
<style>
    /* Base styles */
    .section {
        background: var(--section-bg-color);
        border: 1px solid var(--section-border-color);
        border-radius: 10px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: var(--section-shadow);
    }
    
    .card {
        background: var(--card-bg-color);
        border: 1px solid var(--card-border-color);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: var(--card-shadow);
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: var(--card-shadow-hover);
    }
    
    .section-title {
        color: var(--primary-color);
        font-size: 1.8rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary-color);
    }
    
    h3 {
        color: var(--text-color);
        font-size: 1.4rem;
        margin-bottom: 1rem;
    }
    
    p {
        color: var(--text-color);
    }
    
    /* Light theme variables */
    [data-theme="light"] {
        --primary-color: #2196F3;
        --section-bg-color: #ffffff;
        --section-border-color: #e0e0e0;
        --section-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        --card-bg-color: #f8f9fa;
        --card-border-color: #e0e0e0;
        --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        --card-shadow-hover: 0 4px 8px rgba(0, 0, 0, 0.15);
        --text-color: #2C3E50;
    }
    
    /* Dark theme variables */
    [data-theme="dark"] {
        --primary-color: #90CAF9;
        --section-bg-color: #1E1E1E;
        --section-border-color: #404040;
        --section-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        --card-bg-color: #262730;
        --card-border-color: #404040;
        --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        --card-shadow-hover: 0 4px 8px rgba(0, 0, 0, 0.4);
        --text-color: #E0E0E0;
    }
    
    /* Dataframe styling */
    .dataframe {
        border: none !important;
        background: var(--card-bg-color) !important;
        color: var(--text-color) !important;
    }
    
    .dataframe th {
        background-color: var(--section-bg-color) !important;
        color: var(--primary-color) !important;
        font-weight: 600 !important;
    }
    
    .dataframe td {
        color: var(--text-color) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--card-shadow-hover) !important;
    }
    
    /* Success message styling */
    .success {
        color: #4CAF50 !important;
        font-weight: 500;
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        color: var(--primary-color) !important;
        font-size: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Header section
st.markdown("""
<div class="section">
    <h1 class="section-title">📊 Item Code Matcher</h1>
    <div class="card">
        <p>Welcome to the Item Code Matcher! This tool helps you match your system's item codes with supplier codes using intelligent fuzzy matching.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Instructions section
st.markdown("""
<div class="section">
    <h2 class="section-title">🚀 Quick Start Guide</h2>
    <div class="card">
        <ol>
            <li><strong>Prepare Your Files</strong>
                <ul>
                    <li>Supplier's Excel file with item codes and cost prices</li>
                    <li>Your system's data feed with internal item codes</li>
                </ul>
            </li>
            <li><strong>Upload & Configure</strong>
                <ul>
                    <li>Upload both files in the sections below</li>
                    <li>Select the corresponding columns for matching</li>
                </ul>
            </li>
            <li><strong>Review Results</strong>
                <ul>
                    <li>View all matches with their similarity scores</li>
                    <li>Export results to CSV for further analysis</li>
                </ul>
            </li>
        </ol>
    </div>
</div>
""", unsafe_allow_html=True)

# File upload section
st.markdown("""
<div class="section">
    <h2 class="section-title">📁 Upload Your Files</h2>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <h3>📈 Supplier's File</h3>
        <p>Upload your supplier's Excel file containing item codes and prices.</p>
    </div>
    """, unsafe_allow_html=True)
    supplier_file = st.file_uploader("Upload supplier's Excel file", type=['xlsx', 'xls'])
    if supplier_file:
        st.success(f"✅ Uploaded: {supplier_file.name}")

with col2:
    st.markdown("""
    <div class="card">
        <h3>🗄️ Your System's Data</h3>
        <p>Upload your system's data file with internal item codes.</p>
    </div>
    """, unsafe_allow_html=True)
    system_file = st.file_uploader("Upload your system's data file", type=['xlsx', 'xls', 'csv'])
    if system_file:
        st.success(f"✅ Uploaded: {system_file.name}")

# Process files when both are uploaded
if supplier_file and system_file:
    try:
        # Read the files
        supplier_df = pd.read_excel(supplier_file)
        if system_file.name.endswith('.csv'):
            system_df = pd.read_csv(system_file)
        else:
            system_df = pd.read_excel(system_file)

        # Column selection
        st.markdown("""
        <div class="section">
            <h2 class="section-title">⚙️ Configure Columns</h2>
            <div class="card">
                <p>Select the corresponding columns from your files for matching.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="card">
                <h3>Supplier File Columns</h3>
            </div>
            """, unsafe_allow_html=True)
            supplier_item_col = st.selectbox(
                "Select supplier's item code column",
                supplier_df.columns.tolist()
            )
            supplier_price_col = st.selectbox(
                "Select supplier's price column",
                supplier_df.columns.tolist()
            )

        with col2:
            st.markdown("""
            <div class="card">
                <h3>Your System Columns</h3>
            </div>
            """, unsafe_allow_html=True)
            system_item_col = st.selectbox(
                "Select your system's item code column",
                system_df.columns.tolist()
            )

        if st.button("Start Matching", type="primary"):
            st.markdown("""
            <div class="section">
                <h2 class="section-title">📊 Matching Results</h2>
                <div class="card">
                    <p>Processing your files and finding the best matches...</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Prepare results list
            results = []
            total_items = len(system_df)

            # Perform matching
            for idx, system_row in system_df.iterrows():
                system_code = str(system_row[system_item_col])
                best_match = None
                best_score = 0
                best_price = None

                # Update progress
                progress = (idx + 1) / total_items
                progress_bar.progress(progress)
                status_text.text(f"Processing item {idx + 1} of {total_items}")

                def normalize_code(code):
                    # Convert to string and lowercase
                    code = str(code).lower()
                    # Remove special characters but keep spaces initially
                    code_clean = re.sub(r'[^\w\s]', '', code)
                    # Create variations of the code
                    variations = [
                        code,  # Original lowercase
                        code_clean,  # Without special characters
                        code_clean.replace(' ', ''),  # Without spaces
                        re.sub(r'\s+', '', code)  # Original without spaces
                    ]
                    return variations

                def get_best_match_score(str1_variations, str2_variations):
                    best_score = 0
                    for var1 in str1_variations:
                        for var2 in str2_variations:
                            # Try different matching algorithms
                            ratio_score = fuzz.ratio(var1, var2)
                            token_score = fuzz.token_sort_ratio(var1, var2)
                            partial_score = fuzz.partial_ratio(var1, var2)
                            
                            # Take the highest score from any method
                            best_score = max(best_score, ratio_score, token_score, partial_score)
                    return best_score

                # Find best match for each system item code
                system_variations = normalize_code(system_code)
                
                for _, supplier_row in supplier_df.iterrows():
                    supplier_code = str(supplier_row[supplier_item_col])
                    supplier_variations = normalize_code(supplier_code)
                    
                    score = get_best_match_score(system_variations, supplier_variations)
                    
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

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Create results DataFrame
            results_df = pd.DataFrame(results)
            
            # Sort results by match score in descending order
            results_df = results_df.sort_values('Match Score', ascending=False)
            
            # Format the numeric columns
            results_df['Match Score'] = results_df['Match Score'].astype(float).round(1)
            results_df['Cost Price'] = results_df['Cost Price'].astype(float).round(2)
            
            # Add the % and $ symbols
            results_df['Match Score'] = results_df['Match Score'].astype(str) + '%'
            results_df['Cost Price'] = '$' + results_df['Cost Price'].astype(str)

            # Calculate metrics
            high_matches = len(results_df[results_df['Match Score'].astype(str).str.rstrip('%').astype(float) >= 90])
            medium_matches = len(results_df[results_df['Match Score'].astype(str).str.rstrip('%').astype(float).between(70, 89)])
            low_matches = len(results_df[results_df['Match Score'].astype(str).str.rstrip('%').astype(float) < 70])

            # Display metrics
            st.markdown("""
            <div class="card">
                <h3>Match Quality Summary</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("High Matches (90%+)", high_matches)
            with col2:
                st.metric("Medium Matches (70-89%)", medium_matches)
            with col3:
                st.metric("Low Matches (<70%)", low_matches)

            # Display results
            st.markdown("""
            <div class="card">
                <h3>Detailed Results</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(results_df, height=400, use_container_width=True)

            # Export functionality
            st.markdown("""
            <div class="card">
                <h3>💾 Export Results</h3>
                <p>Download the complete results for further analysis.</p>
            </div>
            """, unsafe_allow_html=True)
            
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name="matching_results.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"An error occurred while processing the files: {str(e)}")
else:
    st.info("Please upload both files to begin matching")
