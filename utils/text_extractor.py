import pypdf
import docx
import io

def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.type
    
    try:
        if file_type == "application/pdf":
            return extract_pdf(uploaded_file)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_docx(uploaded_file)
        elif file_type in ["text/plain", "text/markdown"]:
            return str(uploaded_file.read(), "utf-8")
        else:
            return str(uploaded_file.read(), "utf-8")
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_pdf(file):
    pdf_reader = pypdf.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_docx(file):
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text
