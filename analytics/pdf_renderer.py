import os
import markdown
from xhtml2pdf import pisa

def generate_pdf(md_path: str, pdf_path: str) -> None:
    """
    Presentation Layer purely responsible for rendering the Markdown into an Executive-ready PDF.
    Performs ZERO analytics, business logic, or content generation.
    """
    
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown report not found: {md_path}")
        
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
        
    # Convert Markdown to HTML. Include tables extension for markdown tables.
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    
    # Define Executive CSS styling.
    # Note: xhtml2pdf supports a subset of CSS3. 
    # @page defines the page size, margins, and page breaks.
    css = """
    @page {
        size: letter portrait;
        margin: 2cm;
        @frame footer_frame {
            -pdf-frame-content: footer_content;
            left: 50pt; width: 512pt; top: 772pt; height: 20pt;
        }
    }
    body {
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11pt;
        color: #333333;
        line-height: 1.5;
    }
    h1 {
        color: #1a365d;
        font-size: 24pt;
        border-bottom: 2px solid #2b6cb0;
        padding-bottom: 5px;
        margin-bottom: 20px;
        page-break-before: always;
    }
    h2 {
        color: #2c5282;
        font-size: 18pt;
        margin-top: 30px;
        margin-bottom: 15px;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 3px;
        page-break-after: avoid;
    }
    /* Don't break before the very first H1 */
    body > h1:first-child {
        page-break-before: auto;
    }
    /* Force page break before each H2 to isolate sections as requested for executive readability */
    h2 {
        page-break-before: always;
    }
    p {
        margin-bottom: 12px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
        margin-bottom: 25px;
        font-size: 10pt;
    }
    th {
        background-color: #ebf8ff;
        color: #2b6cb0;
        font-weight: bold;
        text-align: left;
        padding: 8px;
        border: 1px solid #cbd5e0;
    }
    td {
        padding: 8px;
        border: 1px solid #cbd5e0;
    }
    blockquote {
        margin: 15px 0;
        padding: 10px 20px;
        background-color: #f7fafc;
        border-left: 5px solid #4299e1;
        font-style: italic;
    }
    strong {
        color: #2d3748;
    }
    em {
        color: #718096;
    }
    """
    
    # Wrap the HTML with the basic structure required by xhtml2pdf
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            {css}
        </style>
    </head>
    <body>
        <div id="footer_content" style="text-align: right; color: #a0aec0; font-size: 9pt;">
            Forecast Decision Engine - Confidential | Page <pdf:pagenumber> of <pdf:pagecount>
        </div>
        {html_content}
    </body>
    </html>
    """
    
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    with open(pdf_path, "wb") as result_file:
        pisa_status = pisa.CreatePDF(
            src=full_html,
            dest=result_file
        )
        
    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed: {pisa_status.err}")
        
    print(f"Executive PDF generated at: {pdf_path}")
