import os
import re
from typing import List, Dict, Any
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from fpdf import FPDF

SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]

def export_to_google_docs(report_markdown: str, title: str) -> str:
    """
    Creates a Google Doc from the markdown report, applies native formatting,
    and returns the public shareable URL.
    """
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set or file not found.")

    creds = Credentials.from_service_account_file(cred_path, scopes=SCOPES)
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # 1. Create a new Google Doc
    doc = docs_service.documents().create(body={"title": title}).execute()
    document_id = doc.get("documentId")

    # 2. Parse markdown
    current_index = 1
    
    def extract_spans(text):
        bolds = []
        citations = []
        # Extract bold
        while True:
            m = re.search(r'\*\*(.*?)\*\*', text)
            if not m: break
            start = m.start()
            end = start + len(m.group(1))
            bolds.append((start, end))
            text = text[:m.start()] + m.group(1) + text[m.end():]
            
        # Extract citations
        for m in re.finditer(r'\[\d+\]', text):
            citations.append((m.start(), m.end()))
            
        return text, bolds, citations

    paragraphs = []
    tables = []
    
    lines = report_markdown.split("\n")
    in_table = False
    table_rows = []
    
    for line in lines:
        if line.strip().startswith("|") and "|" in line[1:]:
            if not in_table:
                in_table = True
                table_rows = []
            if re.match(r'^[\s\|-]*$', line):
                continue
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            table_rows.append(cells)
        else:
            if in_table:
                tables.append(table_rows)
                in_table = False
                table_rows = []
                paragraphs.append({"type": "table_placeholder"})
            paragraphs.append({"type": "text", "raw": line})
            
    if in_table:
        tables.append(table_rows)
        paragraphs.append({"type": "table_placeholder"})

    plain_text = ""
    style_requests = []
    
    # 3. Build text insertions and format requests
    for p in paragraphs:
        if p["type"] == "table_placeholder":
            continue
            
        line = p["raw"]
        heading_style = "NORMAL_TEXT"
        is_bullet = False
        
        if line.startswith("### "):
            heading_style = "HEADING_3"
            line = line[4:]
        elif line.startswith("## "):
            heading_style = "HEADING_2"
            line = line[3:]
        elif line.startswith("# "):
            heading_style = "HEADING_1"
            line = line[2:]
        elif line.startswith("- ") or line.startswith("* "):
            is_bullet = True
            line = line[2:]
            
        clean_line, bolds, citations = extract_spans(line)
        clean_line += "\n"
        
        start_idx = current_index
        end_idx = current_index + len(clean_line)
        
        plain_text += clean_line
        
        if heading_style != "NORMAL_TEXT":
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start_idx, "endIndex": end_idx},
                    "paragraphStyle": {"namedStyleType": heading_style},
                    "fields": "namedStyleType"
                }
            })
            
        if is_bullet:
            style_requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": start_idx, "endIndex": end_idx},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                }
            })
            
        for b_start, b_end in bolds:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start_idx + b_start, "endIndex": start_idx + b_end},
                    "textStyle": {"bold": True},
                    "fields": "bold"
                }
            })
            
        for c_start, c_end in citations:
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start_idx + c_start, "endIndex": start_idx + c_end},
                    "textStyle": {"foregroundColor": {"color": {"rgbColor": {"blue": 1.0}}}},
                    "fields": "foregroundColor"
                }
            })
            
        current_index = end_idx

    # Execute text insertion and styling
    if plain_text:
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": plain_text
                }
            }
        ]
        requests.extend(style_requests)
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()

    # 4. Insert and populate actual Google Docs tables
    for table_rows in tables:
        # Create table at the end of the document
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": [{"insertTable": {"rows": len(table_rows), "columns": len(table_rows[0]), "endOfSegmentLocation": {}}}]}
        ).execute()
        
        # Fetch document to find the newly assigned cell indices
        doc = docs_service.documents().get(documentId=document_id).execute()
        content = doc.get("body").get("content")
        
        table = None
        for element in reversed(content):
            if "table" in element:
                table = element["table"]
                break
                
        if table:
            cell_requests = []
            # Populate backwards to avoid index shifting
            for r_idx in range(len(table_rows) - 1, -1, -1):
                row = table["tableRows"][r_idx]
                for c_idx in range(len(table_rows[r_idx]) - 1, -1, -1):
                    cell = row["tableCells"][c_idx]
                    start_index = cell["startIndex"] + 1
                    text = table_rows[r_idx][c_idx]
                    if text:
                        cell_requests.append({
                            "insertText": {
                                "location": {"index": start_index},
                                "text": text
                            }
                        })
            if cell_requests:
                docs_service.documents().batchUpdate(documentId=document_id, body={"requests": cell_requests}).execute()

    # 5. Share with public "anyone with link can view"
    drive_service.permissions().create(
        fileId=document_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return f"https://docs.google.com/document/d/{document_id}/view"


def export_to_pdf(report_markdown: str, filename: str) -> str:
    """
    Exports the markdown report to a PDF file locally using fpdf2.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    
    # Strip basic markdown for plain PDF rendering, normalize quotes
    text = report_markdown.replace("’", "'").replace("‘", "'").replace("”", '"').replace("“", '"')
    text = text.replace("–", "-").replace("—", "-").replace("…", "...")
    text = text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 7, text)
    pdf.output(filename)
    return filename


def main():
    sample_markdown = """# AI Agent Research Report
## TL;DR
This is a demonstration of the new **export capabilities**. We can render **bold** text and map [1] citations dynamically.

### Key Findings
- Finding one shows robust RAG generation.
- Finding two validates the Google Docs API parser.

## References
| # | URL | Accessed |
|---|---|---|
| [1] | https://example.com/ai-agents | 2026-05-14 |
| [2] | https://example.com/langgraph | 2026-05-14 |
"""

    print("Testing PDF export...")
    pdf_file = "test_report.pdf"
    export_to_pdf(sample_markdown, pdf_file)
    print(f"PDF successfully exported to {pdf_file}")
    
    print("\nTesting Google Docs export...")
    try:
        url = export_to_google_docs(sample_markdown, "Test Research Report - 2026")
        print(f"Google Docs successfully exported!\nShareable URL: {url}")
    except Exception as e:
        print(f"Google Docs export failed (Please ensure GOOGLE_APPLICATION_CREDENTIALS is valid): {e}")

if __name__ == "__main__":
    main()
