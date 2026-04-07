import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Optional: For PDF export using fpdf2 (modern version)
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

def convert_df_to_pdf(df):
    """
    Simple PDF converter for the dataframe.
    """
    if FPDF is None:
        return None
    
    try:
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("helvetica", size=10)
        
        # Title
        pdf.cell(0, 10, txt="Merged Data Report Preview (First 100 rows)", ln=True, align='C')
        pdf.ln(10)
        
        # Limit data for PDF to prevent memory issues
        display_df = df.head(100).fillna('') 
        cols = display_df.columns.tolist()
        
        # Calculate column width
        col_width = (pdf.w - 20) / max(len(cols), 1)
        
        # Headers
        pdf.set_font("helvetica", 'B', size=8)
        for col in cols:
            pdf.cell(col_width, 10, str(col)[:15], border=1)
        pdf.ln()
        
        # Data rows
        pdf.set_font("helvetica", size=7)
        for i in range(len(display_df)):
            for col in cols:
                val = str(display_df.iloc[i][col])
                pdf.cell(col_width, 10, val[:15], border=1)
            pdf.ln()
            
        return pdf.output()
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")
        return None

def main():
    st.set_page_config(page_title="Data Merger Pro", layout="wide", page_icon="📊")
    
    st.title("📊 Universal Data Merger")
    st.markdown("""
    Upload multiple files with the **same header structure** to combine them into a single file. 
    Supports `.xlsx`, `.csv`, and `.tsv`.
    """)

    # --- Step 1: Upload ---
    st.sidebar.header("Upload Files")
    uploaded_files = st.file_uploader(
        "Select Excel, CSV or TSV files", 
        type=['xlsx', 'csv', 'tsv'], 
        accept_multiple_files=True
    )

    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} files uploaded.")
        
        with st.expander("View uploaded file names"):
            for f in uploaded_files:
                st.write(f"- {f.name}")

        # Persistent storage for merged data in session state
        if 'merged_df' not in st.session_state:
            st.session_state.merged_df = None

        # --- Step 2: Processing ---
        if st.button("🚀 Merge Files", use_container_width=True):
            all_dataframes = []
            reference_columns = None
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, file in enumerate(uploaded_files):
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing: {file.name}")
                
                try:
                    if file.name.endswith('.xlsx'):
                        excel_data = pd.ExcelFile(file)
                        for sheet_name in excel_data.sheet_names:
                            df = pd.read_excel(excel_data, sheet_name=sheet_name)
                            if not df.empty:
                                if reference_columns is None:
                                    reference_columns = list(df.columns)
                                    all_dataframes.append(df)
                                elif list(df.columns) == reference_columns:
                                    all_dataframes.append(df)
                                else:
                                    st.warning(f"Header mismatch: {file.name} (Sheet: {sheet_name})")
                    
                    elif file.name.endswith(('.csv', '.tsv')):
                        sep = '\t' if file.name.endswith('.tsv') else ','
                        df = pd.read_csv(file, sep=sep)
                        if not df.empty:
                            if reference_columns is None:
                                reference_columns = list(df.columns)
                                all_dataframes.append(df)
                            elif list(df.columns) == reference_columns:
                                all_dataframes.append(df)
                            else:
                                st.warning(f"Header mismatch: {file.name}")
                                
                except Exception as e:
                    st.error(f"Error reading {file.name}: {e}")

            status_text.text("Merging complete!")
            
            if all_dataframes:
                st.session_state.merged_df = pd.concat(all_dataframes, axis=0, ignore_index=True)
                st.success(f"Successfully merged {len(all_dataframes)} sources into {len(st.session_state.merged_df)} rows.")
            else:
                st.error("No compatible data was found.")

        # --- Step 3: Display & Downloads ---
        if st.session_state.merged_df is not None:
            merged_df = st.session_state.merged_df
            
            st.subheader("Preview (First 100 rows)")
            st.dataframe(merged_df.head(100), use_container_width=True)
            
            st.subheader("📥 Download Results")
            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')

            # Excel
            buffer_xlsx = io.BytesIO()
            with pd.ExcelWriter(buffer_xlsx, engine='xlsxwriter') as writer:
                merged_df.to_excel(writer, index=False, sheet_name='MergedData')
            d_col1.download_button("Download XLSX", buffer_xlsx.getvalue(), f"merged_{timestamp}.xlsx", "application/vnd.ms-excel")
            
            # CSV
            d_col2.download_button("Download CSV", merged_df.to_csv(index=False).encode('utf-8'), f"merged_{timestamp}.csv", "text/csv")
            
            # TSV
            d_col3.download_button("Download TSV", merged_df.to_csv(index=False, sep='\t').encode('utf-8'), f"merged_{timestamp}.tsv", "text/tab-separated-values")
            
            # PDF
            if FPDF:
                pdf_bytes = convert_df_to_pdf(merged_df)
                if pdf_bytes:
                    d_col4.download_button("Download PDF Preview", pdf_bytes, f"merged_{timestamp}.pdf", "application/pdf")
            else:
                d_col4.warning("Install fpdf2 for PDF")

    else:
        st.info("👈 Please upload files in the sidebar to begin.")

if __name__ == "__main__":
    main()
