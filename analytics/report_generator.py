import os
from content.models import ContentContract, ReportSection, ReportTable, ChartDescriptor

def _render_table(table: ReportTable) -> str:
    if not table.headers or not table.rows:
        return ""
    
    header_line = "| " + " | ".join(str(h) for h in table.headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in table.headers) + " |"
    
    row_lines = []
    for row in table.rows:
        row_lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
        
    return "\n".join([header_line, separator_line] + row_lines) + "\n"

def _render_section(section: ReportSection, is_executive: bool = False) -> str:
    lines = []
    
    # Title
    heading_level = "#" if is_executive else "##"
    lines.append(f"{heading_level} {section.title}\n")
    
    if section.business_question:
        lines.append(f"> **Business Question:** {section.business_question}\n")
        
    if section.is_condensed:
        if section.observation:
            lines.append(f"**Observation:** {section.observation}")
        if section.primary_evidence:
            ev = section.primary_evidence[0]
            lines.append(f"**Evidence:** {ev.name}: {ev.value}")
        if section.conclusion:
            lines.append(f"**Conclusion:** {section.conclusion}")
        if section.decision_support:
            lines.append(f"**Decision Support:** {section.decision_support}")
            
        if section.business_question and not section.recommendation_suppressed and section.recommendation:
            lines.append(f"**Recommendation:** {section.recommendation}")
    else:
        if section.observation:
            lines.append(f"**Observation:** {section.observation}\n")
            
        if section.primary_evidence:
            lines.append("**Primary Evidence:**")
            for ev in section.primary_evidence:
                lines.append(f"- **{ev.name}:** {ev.value}")
            lines.append("")
                
        if section.supporting_evidence:
            lines.append("**Supporting Evidence:**")
            for ev in section.supporting_evidence:
                lines.append(f"- **{ev.name}:** {ev.value}")
            lines.append("")
                
        if section.conclusion:
            lines.append(f"**Conclusion:** {section.conclusion}\n")
            
        if section.decision_support:
            lines.append(f"**Decision Support:** {section.decision_support}\n")
            
        if section.business_question and not section.recommendation_suppressed and section.recommendation:
            lines.append(f"**Recommendation:** {section.recommendation}\n")
                
    lines.append("") # Empty line for spacing
    
    # Charts (Placeholder rendering for PDF generation downstream)
    for chart in section.charts:
        lines.append(f"*(Chart Placeholder: [{chart.chart_type}] {chart.title} - {chart.description})*\n")
        
    # Tables
    for table in section.tables:
        lines.append(_render_table(table))
        
    # Appendix References
    for ref in section.appendix_references:
        lines.append(f"*{ref}*")
        
    return "\n".join(lines)

def generate_report(document: ContentContract, out_md_path: str) -> None:
    """
    Presentation Layer purely responsible for rendering the ContentContract to Markdown.
    Performs ZERO analytics, business logic, or content generation.
    """
    os.makedirs(os.path.dirname(out_md_path), exist_ok=True)
    
    sections = []
    
    # 1. Executive Summary
    if document.executive_summary:
        sections.append(_render_section(document.executive_summary, is_executive=True))
        
    # 2. Q1 Assessment
    if document.q1_assessment:
        sections.append(_render_section(document.q1_assessment))
        
    # 3. Q2 Evaluation
    if document.q2_evaluation:
        sections.append(_render_section(document.q2_evaluation))
        
    # 4. Q3 Actuals
    if document.q3_actuals:
        sections.append(_render_section(document.q3_actuals))
        
    # 5. Q4 Drivers
    if document.q4_drivers:
        sections.append(_render_section(document.q4_drivers))
        
    # 6. Appendix
    if document.appendix:
        sections.append(_render_section(document.appendix))
        
    # Combine all sections
    full_markdown = "\n\n---\n\n".join(sections)
    
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(full_markdown)
