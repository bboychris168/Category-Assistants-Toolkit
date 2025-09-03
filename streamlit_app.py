import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import io

# Set page config
st.set_page_config(
    page_title="Price Impact item code catcher",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main > div {
        padding: 2rem;
        border-radius: 10px;
        background: #ffffff;
    }
    
    /* Headers */
    h1 {
        color: #1E88E5;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 2rem !important;
        padding-bottom: 1rem;
        border-bottom: 3px solid #1E88E5;
    }
    
    h2 {
        color: #2196F3;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
    }
    
    h3 {
        color: #42A5F5;
        font-size: 1.4rem !important;
        font-weight: 500 !important;
    }
    
    /* File uploader */
    .uploadedFile {
        border: 2px dashed #90CAF9;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #2196F3;
    }
    
    /* Dataframe */
    .dataframe {
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .dataframe th {
        background-color: #E3F2FD !important;
        color: #1E88E5 !important;
    }
    
    .dataframe td {
        font-size: 1rem !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
    }
    
    /* Cards */
    .card {
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        margin: 1rem 0;
        background: #FAFAFA;
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0 !important;
        border-color: #E3F2FD !important;
    }
</style>
""", unsafe_allow_html=True)

# Main title with modern styling
st.title("📊 Smart Item Code Matcher")

# Introduction
st.markdown("""
<div class="card">
    <h3>Welcome to Smart Item Code Matcher! 👋</h3>
    <p>This tool helps you match your system's item codes with supplier codes using intelligent fuzzy matching.
    It handles different formats, special characters, and variations to find the best possible matches.</p>
</div>
""", unsafe_allow_html=True)

# Instructions with modern styling
st.markdown("""
<div class="card">
    <h3>🚀 Quick Start Guide</h3>
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
""", unsafe_allow_html=True)

st.markdown("---")

# File upload section with modern styling
st.markdown("""
<h2>📁 Upload Your Files</h2>
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

        st.markdown("---")
        st.header("2️⃣ Configure Column Mapping")

        # Column selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Supplier File Columns")
            supplier_item_col = st.selectbox(
                "Select supplier's item code column",
                supplier_df.columns.tolist()
            )
            supplier_price_col = st.selectbox(
                "Select supplier's price column",
                supplier_df.columns.tolist()
            )

        with col2:
            st.subheader("Your System Columns")
            system_item_col = st.selectbox(
                "Select your system's item code column",
                system_df.columns.tolist()
            )

        # Start matching process
        st.markdown("---")
        st.header("3️⃣ Results")
        
        if st.button("Start Matching", type="primary"):

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
            
            # Results summary with metrics
            st.markdown("""
            <div class="card">
                <h3>🎯 Matching Results Summary</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            # Calculate metrics
            high_matches = len(results_df[results_df['Match Score'].astype(str).str.rstrip('%').astype(float) >= 90])
            medium_matches = len(results_df[results_df['Match Score'].astype(str).str.rstrip('%').astype(float).between(70, 89)])
            low_matches = len(results_df[results_df['Match Score'].astype(str).str.rstrip('%').astype(float) < 70])
            
            with col1:
                st.metric("High Matches (90%+)", high_matches)
            with col2:
                st.metric("Medium Matches (70-89%)", medium_matches)
            with col3:
                st.metric("Low Matches (<70%)", low_matches)
            
            # Format the numeric columns
            results_df['Match Score'] = results_df['Match Score'].astype(float).round(1)
            results_df['Cost Price'] = results_df['Cost Price'].astype(float).round(2)
            
            # Add the % and $ symbols
            results_df['Match Score'] = results_df['Match Score'].astype(str) + '%'
            results_df['Cost Price'] = '$' + results_df['Cost Price'].astype(str)
            
            # Display the dataframe with styling
            st.markdown("""
            <div class="card">
                <h3>📊 Detailed Results</h3>
                <p>Scroll through all matches below, sorted by match score (highest first).</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(
                results_df,
                height=400,
                use_container_width=True
            )

            # Export functionality with enhanced styling
            st.markdown("""
            <div class="card">
                <h3>💾 Export Your Results</h3>
                <p>Download the complete results as a CSV file for further analysis.</p>
            </div>
            """, unsafe_allow_html=True)
            
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name="matching_results.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"An error occurred while processing the files: {str(e)}")
else:
    st.info("Please upload both files to begin matching")
