import os
import sys
from pathlib import Path
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, 
    PageBreak, KeepTogether, ListFlowable, ListItem
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas class to dynamically compute and render 'Page X of Y' page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Don't draw headers/footers on the cover page (Page 1)
        if self._pageNumber == 1:
            self.restoreState()
            return
            
        # Margins & Bounds
        left_margin = 0.75 * inch
        right_margin = 8.5 * inch - 0.75 * inch
        top_y = 11 * inch - 0.5 * inch
        bottom_y = 0.5 * inch
        
        # Header Accent Line & Text
        self.setStrokeColor(colors.HexColor('#1a365d'))
        self.setLineWidth(0.75)
        self.line(left_margin, top_y - 15, right_margin, top_y - 15)
        
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.HexColor('#4a5568'))
        self.drawString(left_margin, top_y - 10, "VerifAI Technical Design Overview & Architecture Portfolio")
        self.drawRightString(right_margin, top_y - 10, "High-Compliance RAG Systems")
        
        # Footer Page Numbers & Disclaimer
        self.line(left_margin, bottom_y + 15, right_margin, bottom_y + 15)
        self.drawString(left_margin, bottom_y + 5, "CONFIDENTIAL & PROPRIETARY — FOR AI-FIRST PRODUCT REVIEW")
        self.drawRightString(right_margin, bottom_y + 5, f"Page {self._pageNumber} of {page_count}")
        
        self.restoreState()

def build_pdf(md_path: Path, img_path: Path, output_path: Path):
    print("Reading and parsing Markdown portfolio...")
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Document setup
    pdf_filename = str(output_path)
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch
    )

    # Base Styles
    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor('#1a365d')   # Deep Blue
    c_secondary = colors.HexColor('#2b6cb0') # Accent Slate Blue
    c_text = colors.HexColor('#2d3748')      # Dark Grey Body
    c_sub = colors.HexColor('#718096')       # Muted Slate
    c_bg_light = colors.HexColor('#f7fafc')  # Table / Callout Background

    # Define Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=c_primary,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=16,
        leading=22,
        textColor=c_secondary,
        spaceAfter=30
    )
    
    metadata_style = ParagraphStyle(
        'CoverMetadata',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=c_text,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        textColor=c_primary,
        spaceBefore=22,
        spaceAfter=12,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_secondary,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'H3',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_primary,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14.5,
        textColor=c_text,
        spaceAfter=10
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=6
    )
    
    bullet_nested_style = ParagraphStyle(
        'BulletNested',
        parent=bullet_style,
        leftIndent=30,
        firstLineIndent=-10,
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1 # Center
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=c_text,
        alignment=1 # Center
    )

    table_cell_left_style = ParagraphStyle(
        'TableCellLeft',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=c_text,
        alignment=0 # Left
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_primary,
        leftIndent=15,
        rightIndent=15,
        spaceBefore=8,
        spaceAfter=8
    )

    story = []

    # -------------------------------------------------------------------------
    # COVER PAGE
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("VerifAI Evidence Substantiation Pipeline", title_style))
    story.append(Paragraph("Technical Design Overview & Architecture Portfolio", subtitle_style))
    
    # Visual accent bar
    story.append(Table(
        [['']], 
        colWidths=[7.0 * inch], 
        rowHeights=[4], 
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_primary),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ])
    ))
    story.append(Spacer(1, 0.4 * inch))
    
    story.append(Paragraph("<b>Domain:</b> Healthcare Regulatory Affairs & High-Compliance RAG Systems", metadata_style))
    story.append(Paragraph("<b>Author:</b> Lead AI Systems Architect", metadata_style))
    story.append(Paragraph("<b>Scale:</b> Multi-Agent LLM Judge Engine & Hybrid Reciprocal Rank Fusion Store", metadata_style))
    story.append(Paragraph("<b>Version:</b> 1.1 (Production Design Overview)", metadata_style))
    story.append(Paragraph("<b>Date:</b> May 20, 2026", metadata_style))
    
    story.append(Spacer(1, 1.8 * inch))
    
    # Modern cover page border box
    story.append(Table(
        [[
            Paragraph(
                "<i>This portfolio presentation details the technical implementation, clinical RAG ingestion pipelines, "
                "multi-agent arbitration models, and deterministic logic gate frameworks built for pharmaceutical "
                "evidence verification. Confidentially compiled for an AI-First product direction review.</i>", 
                ParagraphStyle('CoverIntel', parent=body_style, fontName='Helvetica-Oblique', fontSize=10, textColor=c_sub)
            )
        ]],
        colWidths=[7.0 * inch],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
            ('PADDING', (0,0), (-1,-1), 15),
        ])
    ))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # PARSING SYSTEM AND STATE
    # -------------------------------------------------------------------------
    in_mermaid = False
    in_table = False
    table_lines = []
    
    for i, line in enumerate(lines):
        clean_line = line.strip()
        
        # Skip top level file header (since we have a cover page)
        if clean_line.startswith("# Technical Portfolio"):
            continue
            
        # Mermaid code blocks block out
        if clean_line.startswith("```mermaid"):
            in_mermaid = True
            # We replace the Mermaid flow diagram with our high-end digital architecture PNG!
            continue
        elif in_mermaid and clean_line.startswith("```"):
            in_mermaid = False
            # Insert the modern digital architecture diagram
            print("Embedding Substantiation Pipeline Digital Overview Image...")
            if img_path.exists():
                # Original image is high res. Let's size it perfectly to fit page width (7 inches)
                img = Image(str(img_path), width=7.0 * inch, height=3.89 * inch)
                story.append(Spacer(1, 10))
                story.append(img)
                story.append(Spacer(1, 10))
            else:
                story.append(Paragraph("[Missing Architecture Diagram Image: substantiation_pipeline_design.png]", body_style))
            continue
        elif in_mermaid:
            continue
            
        # Standard Markdown Tables detection (e.g. matrices)
        if clean_line.startswith("|") and not in_table:
            # Skip the Markdown table if inside metadata tags
            if i > 0 and lines[i-1].strip().startswith("Routing Matrix") or lines[i-1].strip().startswith("Dynamic rule selection"):
                in_table = True
                table_lines = [clean_line]
                continue
            else:
                # Regular text containing pipe symbols
                pass
        elif in_table and clean_line.startswith("|"):
            table_lines.append(clean_line)
            continue
        elif in_table and not clean_line.startswith("|"):
            in_table = False
            # Render Table
            rendered_table = render_markdown_table(table_lines, table_header_style, table_cell_style, table_cell_left_style, c_primary, c_bg_light)
            if rendered_table:
                story.append(Spacer(1, 6))
                story.append(rendered_table)
                story.append(Spacer(1, 8))
            table_lines = []
            
        # Heading 1
        if clean_line.startswith("## ") and not clean_line.startswith("### "):
            header_text = clean_line[3:].replace("**", "").replace("*", "")
            # Page Break for major headings to look professional
            if header_text in ["1. Professional Profile & Core Portfolios", "2. Technical Presentation: The VerifAI Evidence Substantiation Pipeline", "What Challenges Were Faced?"]:
                story.append(PageBreak())
            story.append(Paragraph(header_text, h1_style))
            continue
            
        # Heading 2
        if clean_line.startswith("### ") and not clean_line.startswith("#### "):
            header_text = clean_line[4:].replace("**", "").replace("*", "")
            story.append(Paragraph(header_text, h2_style))
            continue
            
        # Heading 3
        if clean_line.startswith("#### "):
            header_text = clean_line[5:].replace("**", "").replace("*", "")
            story.append(Paragraph(header_text, h3_style))
            continue
            
        # Blockquotes/Callouts
        if clean_line.startswith("> "):
            blockquote_text = clean_line[2:]
            story.append(Spacer(1, 5))
            story.append(Table(
                [[Paragraph(blockquote_text, callout_style)]],
                colWidths=[7.0 * inch],
                style=TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
                    ('LINELEFT', (0,0), (-1,-1), 3, c_secondary),
                    ('PADDING', (0,0), (-1,-1), 10),
                ])
            ))
            story.append(Spacer(1, 5))
            continue
            
        # Lists (Nested and Standard)
        if clean_line.startswith("    * ") or clean_line.startswith("  * ") or clean_line.startswith("    - ") or clean_line.startswith("  - "):
            list_text = clean_line.split("* ", 1)[-1] if "* " in clean_line else clean_line.split("- ", 1)[-1]
            list_text = format_bold_markdown(list_text)
            story.append(Paragraph(f"&bull; {list_text}", bullet_nested_style))
            continue
            
        if clean_line.startswith("* ") or clean_line.startswith("- "):
            list_text = clean_line[2:]
            list_text = format_bold_markdown(list_text)
            story.append(Paragraph(f"&bull; {list_text}", bullet_style))
            continue
            
        if clean_line.startswith("1. ") or clean_line.startswith("2. ") or clean_line.startswith("3. ") or clean_line.startswith("4. ") or clean_line.startswith("5. ") or clean_line.startswith("6. "):
            list_num = clean_line.split(".", 1)[0]
            list_text = clean_line.split(".", 1)[1].strip()
            list_text = format_bold_markdown(list_text)
            story.append(Paragraph(f"<b>{list_num}.</b> {list_text}", bullet_style))
            continue
            
        # Blank line spacer
        if not clean_line:
            story.append(Spacer(1, 4))
            continue
            
        # Code block marker lines
        if clean_line.startswith("```"):
            continue
            
        # Skip image tags and alternative text since we handle the image natively
        if clean_line.startswith("!["):
            continue
        if clean_line.startswith("*Alternatively, below"):
            continue
            
        # Regular paragraph body
        body_text = format_bold_markdown(clean_line)
        story.append(Paragraph(body_text, body_style))

    # Build document
    print("Compiling PDF...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF Generation complete!")

def format_bold_markdown(text: str) -> str:
    """Translate basic Markdown bold '**text**' to HTML tags '<b>text</b>'."""
    import re
    # Match markdown bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Match markdown italic
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Match code tags
    text = re.sub(r'`(.*?)`', r'<font face="Courier" color="#1a365d"><b>\1</b></font>', text)
    # Match local absolute links
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<font color="#2b6cb0"><u>\1</u></font>', text)
    return text

def render_markdown_table(lines: List[str], header_style: ParagraphStyle, cell_style: ParagraphStyle, cell_left_style: ParagraphStyle, primary_color, bg_light_color) -> Table:
    """Convert raw Markdown table rows into a beautifully formatted ReportLab Table Flowable."""
    if len(lines) < 2:
        return None
        
    table_data = []
    
    # Parse headers
    header_cols = [c.strip() for c in lines[0].split("|")[1:-1]]
    header_row = [Paragraph(f"<b>{col}</b>", header_style) for col in header_cols]
    table_data.append(header_row)
    
    # Parse body
    for line in lines[2:]:
        row_cols = [c.strip() for c in line.split("|")[1:-1]]
        formatted_row = []
        for j, col in enumerate(row_cols):
            # Check if column text contains code snippets or bold
            col_txt = format_bold_markdown(col)
            # Use left alignment for text columns, center for data columns
            style = cell_left_style if j == 0 or len(col) > 15 else cell_style
            formatted_row.append(Paragraph(col_txt, style))
        table_data.append(formatted_row)
        
    if not table_data:
        return None
        
    # Auto column widths fitting
    num_cols = len(header_cols)
    if num_cols == 5:
        # P A C N rule matrices
        widths = [2.0 * inch, 1.25 * inch, 1.25 * inch, 1.25 * inch, 1.25 * inch]
    else:
        # Standard even spacing
        widths = [7.0 * inch / num_cols] * num_cols
        
    t = Table(table_data, colWidths=widths)
    
    # Table Styling
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), primary_color), # Primary Deep Blue header
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    
    # Alternating background colors
    for r in range(1, len(table_data)):
        bg_col = bg_light_color if r % 2 == 1 else colors.white
        t_style.append(('BACKGROUND', (0, r), (-1, r), bg_col))
        
    t.setStyle(TableStyle(t_style))
    return t

if __name__ == '__main__':
    workspace_dir = Path("c:/Users/User/Downloads/new_pipeline/new_pipeline")
    md_file = workspace_dir / "presentation_portfolio.md"
    img_file = workspace_dir / "substantiation_pipeline_design.png"
    pdf_out = workspace_dir / "VerifAI_Evidence_Substantiation_Pipeline_Technical_Design.pdf"
    
    build_pdf(md_file, img_file, pdf_out)
