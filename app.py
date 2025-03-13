import streamlit as st
import os
import tempfile
from script import extract_text_pdf, summarize_text, extract_structured_fields
import base64
from pathlib import Path
import pandas as pd
import csv

# Page configuration
st.set_page_config(
    page_title="PDF Extract - Behaind",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Behaind colors
BEHAIND_BLUE = "#0A2647"
BEHAIND_LIGHT_BLUE = "#7DA5CA"  # Cor mais clara para textos
BEHAIND_WHITE = "#FFFFFF"

# Custom CSS
st.markdown(f"""
    <style>
        .main {{
            padding: 2rem;
            background-color: {BEHAIND_WHITE};
        }}
        .logo-container {{
            margin-bottom: 20px;
        }}
        .logo {{
            max-width: 100px;
            margin-left: 0;
        }}
        .stButton>button {{
            width: 100%;
            border-radius: 10px;
            height: 3em;
            background-color: {BEHAIND_BLUE};
            color: {BEHAIND_WHITE};
            font-weight: bold;
        }}
        .stButton>button:hover {{
            background-color: {BEHAIND_BLUE};
            opacity: 0.9;
        }}
        .upload-header {{
            text-align: center;
            padding: 2rem 0;
            color: {BEHAIND_LIGHT_BLUE};
        }}
        .stProgress > div > div > div {{
            background-color: {BEHAIND_BLUE};
        }}
        .download-header {{
            text-align: center;
            padding: 1rem 0;
            color: {BEHAIND_LIGHT_BLUE};
        }}
        .download-button {{
            display: inline-block;
            padding: 0.5em 1em;
            background-color: {BEHAIND_BLUE};
            color: {BEHAIND_WHITE} !important;
            text-decoration: none;
            border-radius: 5px;
            text-align: center;
            transition: all 0.3s;
        }}
        .download-button:hover {{
            opacity: 0.9;
            text-decoration: none;
        }}
        .title {{
            color: {BEHAIND_LIGHT_BLUE};
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
        }}
        .subtitle {{
            color: {BEHAIND_LIGHT_BLUE};
            text-align: center;
            font-size: 1.2em;
            margin-top: 2em;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {BEHAIND_WHITE};
            color: {BEHAIND_LIGHT_BLUE};
            border-radius: 4px 4px 0px 0px;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {BEHAIND_BLUE} !important;
            color: {BEHAIND_WHITE} !important;
        }}
        .preview-header {{
            color: {BEHAIND_LIGHT_BLUE};
            margin-top: 2em;
        }}
        .footer {{
            text-align: center;
            color: {BEHAIND_LIGHT_BLUE};
            margin-top: 2em;
        }}
    </style>
""", unsafe_allow_html=True)

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}" class="download-button">⬇️ Download {file_label}</a>'
    return href

def parse_fields_to_dict(fields_text):
    """Converts structured text to dictionary."""
    fields = {}
    for line in fields_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            fields[key.strip()] = value.strip()
    return fields

def create_csv(fields_dict, filepath):
    """Creates CSV file with structured fields."""
    fieldnames = [
        'Order date', 'Order number', 'Contract Number', 'Orderer',
        'Billing address', 'Delivery address', 'Supplier address',
        'our range', 'Offer date', 'Delivery date', 'Delivery conditions',
        'Payment terms', 'Remarks', 'Material number Kunde',
        'Material number CCL', 'Material description', 'Drawing number',
        'Crowd', 'Price/unit', 'Price piece', 'net amount', 'Currency',
        'Commodity number'
    ]
    
    field_mapping = {
        'ORDER_DATE': 'Order date',
        'ORDER_NUMBER': 'Order number',
        'CONTRACT_NUMBER': 'Contract Number',
        'ORDERER': 'Orderer',
        'BILLING_ADDRESS': 'Billing address',
        'DELIVERY_ADDRESS': 'Delivery address',
        'SUPPLIER_ADDRESS': 'Supplier address',
        'OUR_RANGE': 'our range',
        'OFFER_DATE': 'Offer date',
        'DELIVERY_DATE': 'Delivery date',
        'DELIVERY_CONDITIONS': 'Delivery conditions',
        'PAYMENT_TERMS': 'Payment terms',
        'REMARKS': 'Remarks',
        'MATERIAL_NUMBER_KUNDE': 'Material number Kunde',
        'MATERIAL_NUMBER_CCL': 'Material number CCL',
        'MATERIAL_DESCRIPTION': 'Material description',
        'DRAWING_NUMBER': 'Drawing number',
        'CROWD': 'Crowd',
        'PRICE_PER_UNIT': 'Price/unit',
        'PRICE_PIECE': 'Price piece',
        'NET_AMOUNT': 'net amount',
        'CURRENCY': 'Currency',
        'COMMODITY_NUMBER': 'Commodity number'
    }
    
    row_dict = {field_mapping[k]: v for k, v in fields_dict.items() if k in field_mapping}
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row_dict)

def main():
    # Logo no canto superior esquerdo
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image("logo.png", width=80)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Subtítulo - movido para a coluna do meio
    with col2:
        st.markdown("<p class='subtitle'>Transform your PDFs into structured data</p>", unsafe_allow_html=True)
    
    # Upload section
    st.markdown("<div class='upload-header'><h3>📤 Upload Document</h3></div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type="pdf")
    
    if uploaded_file is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "uploaded_file.pdf"
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            if st.button("🔍 Analyze Document"):
                with st.spinner('Processing your document...'):
                    progress_bar = st.progress(0)
                    
                    # Extract text
                    progress_bar.progress(20)
                    st.info("📄 Extracting text from PDF...")
                    extracted_text = extract_text_pdf(str(pdf_path))
                    
                    # Extract structured fields
                    progress_bar.progress(40)
                    st.info("🔍 Extracting structured fields...")
                    fields_text = extract_structured_fields(extracted_text)
                    fields_dict = parse_fields_to_dict(fields_text)
                    
                    # Generate summary
                    progress_bar.progress(60)
                    st.info("🤖 Generating detailed analysis...")
                    summary = summarize_text(extracted_text)
                    
                    # Save files
                    progress_bar.progress(80)
                    st.info("💾 Preparing files...")
                    
                    # Save TXT
                    output_txt = Path(temp_dir) / "detailed_analysis.txt"
                    with open(output_txt, "w", encoding="utf-8") as f:
                        f.write(summary)
                    
                    # Save CSV
                    output_csv = Path(temp_dir) / "extracted_fields.csv"
                    create_csv(fields_dict, output_csv)
                    
                    progress_bar.progress(100)
                    st.success("✅ Analysis completed successfully!")
                    
                    # Download area
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("<div class='download-header'><h3>📥 Download Analysis</h3></div>", unsafe_allow_html=True)
                        st.markdown(get_binary_file_downloader_html(output_txt, "Analysis"), unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("<div class='download-header'><h3>📥 Download CSV</h3></div>", unsafe_allow_html=True)
                        st.markdown(get_binary_file_downloader_html(output_csv, "CSV"), unsafe_allow_html=True)
                    
                    # Results preview
                    st.markdown("<h3 class='preview-header'>👀 Preview Results</h3>", unsafe_allow_html=True)
                    
                    tab1, tab2 = st.tabs(["Detailed Analysis", "Structured Fields"])
                    
                    with tab1:
                        st.text_area("", summary, height=300)
                    
                    with tab2:
                        df = pd.read_csv(output_csv)
                        st.dataframe(df)
    
    # Footer atualizado
    st.markdown("---")
    st.markdown("<p class='footer'>Developed by Behaind</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 