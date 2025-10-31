# file: utils.py

import streamlit as st
import pandas as pd
from docx import Document
from pypdf import PdfReader # CORRECTED: Changed from PyPDF2 to pypdf
import io

@st.cache_data(show_spinner="Parsing document...")
def parse_uploaded_file(uploaded_file):
    """
    Parses an uploaded file and returns its text content.
    Supports PDF, DOCX, and XLSX files.
    
    Args:
        uploaded_file: The file object from st.file_uploader.

    Returns:
        A string containing the extracted text, or None if parsing fails.
    """
    if uploaded_file is None:
        return None

    # Get the file extension to determine the parsing method
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == "pdf":
            # Use pypdf to extract text from each page of a PDF
            pdf_reader = PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text

        elif file_extension == "docx":
            # Use python-docx to extract text from paragraphs in a Word document
            document = Document(uploaded_file)
            text = "\n".join([para.text for para in document.paragraphs])
            return text

        elif file_extension == "xlsx":
            # Use pandas and openpyxl to extract text from all sheets in an Excel file
            excel_file = pd.ExcelFile(uploaded_file)
            text = ""
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                # Convert the dataframe to a string, which is useful for the LLM
                df_string = df.to_string(index=False)
                text += f"--- Content from sheet: {sheet_name} ---\n"
                text += df_string + "\n\n"
            return text

        else:
            # If the file format is not supported, show an error
            st.error(f"Unsupported file format: .{file_extension}. Please upload a PDF, DOCX, or XLSX file.")
            return None
            
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None
