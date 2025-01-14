import streamlit as st

# Configure page
st.set_page_config(page_title="RSEA Product Team Tool Kit")
st.title("🎈RSEA Product Team Tool Kit")
st.write("Tool used for RSEA Product team")

# Instructions
st.write("""
### Please upload the following files:
1. **12m Sales - Phocas Export**  
2. **Export - Pronto Export**  
3. **RSEA Price List**  
4. **Suppliers Price List**

✅ **Note:** Files must be Excel files (.xlsx or .xls).

### 📥 Download Templates
You can download templates for each required file below:
         
""")

# File uploader (accept multiple files)
files = st.file_uploader("Upload Excel Files", type=["xlsx", "xls"], accept_multiple_files=True)

# Check if files are uploaded
if files:
    st.success("Files uploaded successfully!")
    for file in files:
        st.write(f"📄 **{file.name}**")
else:
    st.info("Please upload the required files.")
