"""
scanner/reporter.py — PDF report generator
============================================
Generates a professional PDF security report using reportlab.
Replaces the previous HTML reporter — drop-in replacement,
same function signature: generate_report(findings, scan_path, stats, output_path)
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus import Flowable

# ── Colour palette ────────────────────────────────────────────────────────────

CRITICAL_COLOR = colors.HexColor("#e24b4a")
HIGH_COLOR     = colors.HexColor("#ef9f27")
MEDIUM_COLOR   = colors.HexColor("#378add")
LOW_COLOR      = colors.HexColor("#639922")
CLEAN_COLOR    = colors.HexColor("#639922")

CRITICAL_BG    = colors.HexColor("#fff0f0")
HIGH_BG        = colors.HexColor("#fffbf0")
MEDIUM_BG      = colors.HexColor("#f0f6ff")
LOW_BG         = colors.HexColor("#f3faf0")

PAGE_BG        = colors.HexColor("#f5f5f0")
CARD_BG        = colors.white
BORDER_COLOR   = colors.HexColor("#e0dfd8")
TEXT_PRIMARY   = colors.HexColor("#1a1a1a")
TEXT_SECONDARY = colors.HexColor("#666666")
TEXT_MUTED     = colors.HexColor("#999999")
ACCENT_PURPLE  = colors.HexColor("#534ab7")

SEVERITY_COLOR = {
    "CRITICAL": CRITICAL_COLOR,
    "HIGH":     HIGH_COLOR,
    "MEDIUM":   MEDIUM_COLOR,
    "LOW":      LOW_COLOR,
}

SEVERITY_BG = {
    "CRITICAL": CRITICAL_BG,
    "HIGH":     HIGH_BG,
    "MEDIUM":   MEDIUM_BG,
    "LOW":      LOW_BG,
}

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# ── Custom flowables ──────────────────────────────────────────────────────────

class ColoredLine(Flowable):
    """A full-width horizontal rule with a given color and thickness."""
    def __init__(self, color, thickness=0.5, width_pct=1.0):
        super().__init__()
        self.color     = color
        self.thickness = thickness
        self.width_pct = width_pct
        self.height    = thickness + 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        w = self.width * self.width_pct
        self.canv.line(0, self.thickness / 2, w, self.thickness / 2)


class SeverityBadge(Flowable):
    """Pill-shaped severity badge drawn directly on the canvas."""
    def __init__(self, severity, width=70, height=18):
        super().__init__()
        self.severity = severity
        self.width    = width
        self.height   = height

    def draw(self):
        color = SEVERITY_COLOR.get(self.severity, TEXT_MUTED)
        bg    = SEVERITY_BG.get(self.severity, colors.white)
        c     = self.canv

        c.setFillColor(bg)
        c.setStrokeColor(color)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, self.height / 2,
                    fill=1, stroke=1)

        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(self.width / 2, 5, self.severity)


# ── Style helpers ─────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()

    def make(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "title": make("rpt_title",
            fontName="Helvetica-Bold", fontSize=22,
            textColor=TEXT_PRIMARY, leading=28, spaceAfter=4),

        "subtitle": make("rpt_subtitle",
            fontName="Helvetica", fontSize=11,
            textColor=TEXT_SECONDARY, leading=16, spaceAfter=0),

        "section": make("rpt_section",
            fontName="Helvetica-Bold", fontSize=13,
            textColor=TEXT_PRIMARY, leading=18,
            spaceBefore=14, spaceAfter=8),

        "filepath": make("rpt_filepath",
            fontName="Courier-Bold", fontSize=10,
            textColor=ACCENT_PURPLE, leading=14, spaceAfter=4),

        "finding_title": make("rpt_finding_title",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=TEXT_PRIMARY, leading=15),

        "label": make("rpt_label",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=TEXT_SECONDARY, leading=13),

        "body": make("rpt_body",
            fontName="Helvetica", fontSize=9,
            textColor=TEXT_PRIMARY, leading=13),

        "fix": make("rpt_fix",
            fontName="Courier", fontSize=8,
            textColor=colors.HexColor("#1a5c2a"),
            backColor=colors.HexColor("#f0f9f0"),
            leading=13, leftIndent=6, rightIndent=6,
            spaceBefore=2, spaceAfter=2),

        "meta": make("rpt_meta",
            fontName="Helvetica", fontSize=8,
            textColor=TEXT_MUTED, leading=12),

        "clean": make("rpt_clean",
            fontName="Helvetica-Bold", fontSize=13,
            textColor=CLEAN_COLOR, alignment=TA_CENTER,
            leading=20, spaceBefore=24, spaceAfter=8),
    }


# ── Page template (header + footer on every page) ────────────────────────────

def _make_page_template(project_name, scanned_at):
    def on_page(canvas, doc):
        canvas.saveState()
        W, H = A4

        # Top accent bar
        canvas.setFillColor(ACCENT_PURPLE)
        canvas.rect(0, H - 8 * mm, W, 8 * mm, fill=1, stroke=0)

        # Footer rule
        canvas.setStrokeColor(BORDER_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(15 * mm, 14 * mm, W - 15 * mm, 14 * mm)

        # Footer text
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(TEXT_MUTED)
        canvas.drawString(15 * mm, 9 * mm,
                          f"AI Security Scanner  ·  {project_name}  ·  {scanned_at}")
        canvas.drawRightString(W - 15 * mm, 9 * mm,
                               f"Page {doc.page}")
        canvas.restoreState()

    return on_page


# ── Summary table ─────────────────────────────────────────────────────────────

def _summary_table(counts, stats, S):
    col_w = 35 * mm

    def cell(label, value, color, bg):
        return [
            Paragraph(f'<font color="{color.hexval()}">'
                      f'<b>{value}</b></font>', S["finding_title"]),
            Paragraph(f'<font color="{color.hexval()}">{label}</font>',
                      S["label"]),
        ]

    data = [[
        cell("CRITICAL", counts["CRITICAL"], CRITICAL_COLOR, CRITICAL_BG),
        cell("HIGH",     counts["HIGH"],     HIGH_COLOR,     HIGH_BG),
        cell("MEDIUM",   counts["MEDIUM"],   MEDIUM_COLOR,   MEDIUM_BG),
        cell("LOW",      counts["LOW"],      LOW_COLOR,      LOW_BG),
    ]]

    tbl = Table(data, colWidths=[col_w] * 4)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), CRITICAL_BG),
        ("BACKGROUND", (1, 0), (1, 0), HIGH_BG),
        ("BACKGROUND", (2, 0), (2, 0), MEDIUM_BG),
        ("BACKGROUND", (3, 0), (3, 0), LOW_BG),
        ("BOX",        (0, 0), (0, 0), 0.5, CRITICAL_COLOR),
        ("BOX",        (1, 0), (1, 0), 0.5, HIGH_COLOR),
        ("BOX",        (2, 0), (2, 0), 0.5, MEDIUM_COLOR),
        ("BOX",        (3, 0), (3, 0), 0.5, LOW_COLOR),
        ("ROUNDEDCORNERS", [6]),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEBEFORE", (1, 0), (3, 0), 0, colors.white),
    ]))
    return tbl


# ── Single finding card ───────────────────────────────────────────────────────

def _finding_card(finding, S, usable_width):
    severity = finding.get("severity", "LOW")
    color    = SEVERITY_COLOR.get(severity, TEXT_MUTED)
    bg       = SEVERITY_BG.get(severity, colors.white)

    title_row = Table(
        [[
            SeverityBadge(severity, width=58, height=16),
            Paragraph(finding.get("type", "Unknown vulnerability"), S["finding_title"]),
            Paragraph(f'Line {finding.get("line", "?")}', S["meta"]),
        ]],
        colWidths=[62, usable_width - 62 - 40, 40],
    )
    title_row.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (2, 0), (2, 0),   "RIGHT"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    rows = [
        [title_row],
        [Spacer(1, 5)],
        [Paragraph('<b>What: </b>' + finding.get("description", ""), S["body"])],
        [Paragraph('<b>Risk: </b>' + finding.get("risk", ""), S["body"])],
        [Spacer(1, 4)],
        [Paragraph('<b>Fix:</b>', S["label"])],
        [Paragraph(finding.get("fix", ""), S["fix"])],
    ]

    inner = Table(rows, colWidths=[usable_width - 24])
    inner.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    card = Table([[inner]], colWidths=[usable_width])
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("LINEAFTER",     (0, 0), (0, -1),  2, color),   # left accent stripe
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROUNDEDCORNERS", [4]),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    return card


# ── Public API ────────────────────────────────────────────────────────────────

def generate_report(findings, scan_path, stats, output_path):
    """
    Generates a PDF security report.

    findings    : list of finding dicts from analyzer
    scan_path   : root path that was scanned
    stats       : dict from walker.get_file_stats()
    output_path : where to save the .pdf file
    """
    # Ensure .pdf extension
    if not output_path.endswith(".pdf"):
        output_path = output_path.rsplit(".", 1)[0] + ".pdf"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    project    = os.path.basename(os.path.abspath(scan_path))
    scanned_at = datetime.now().strftime("%B %d, %Y at %H:%M")
    counts     = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        s = f.get("severity", "LOW")
        counts[s] = counts.get(s, 0) + 1

    W, H       = A4
    margin     = 15 * mm
    usable_w   = W - 2 * margin

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title=f"Security Scan — {project}",
        author="AI Security Scanner",
    )

    S        = _styles()
    on_page  = _make_page_template(project, scanned_at)
    story    = []

    # ── Cover / header ────────────────────────────────────────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Security scan report", S["title"]))
    story.append(Paragraph(
        f"Project: <b>{project}</b> &nbsp;·&nbsp; "
        f"Scanned: {scanned_at} &nbsp;·&nbsp; "
        f"Files: {stats.get('total_files', 0)} &nbsp;·&nbsp; "
        f"Lines: {stats.get('total_lines', 0):,}",
        S["subtitle"],
    ))
    story.append(Spacer(1, 5 * mm))
    story.append(ColoredLine(BORDER_COLOR))
    story.append(Spacer(1, 5 * mm))

    # ── Summary cards ─────────────────────────────────────────────────────────
    story.append(_summary_table(counts, stats, S))
    story.append(Spacer(1, 8 * mm))

    # ── Findings ──────────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"Findings — {len(findings)} total", S["section"]
    ))

    if not findings:
        story.append(Paragraph("No vulnerabilities found.", S["clean"]))
        story.append(Paragraph(
            "The scanned files look clean.", S["subtitle"]
        ))
    else:
        # Group by file, sort files by worst severity
        grouped = {}
        for f in findings:
            grouped.setdefault(f.get("file", "unknown"), []).append(f)

        def file_priority(item):
            sevs = [f.get("severity", "LOW") for f in item[1]]
            return min(SEVERITY_ORDER.get(s, 3) for s in sevs)

        for filepath, file_findings in sorted(grouped.items(), key=file_priority):
            rel = os.path.relpath(filepath, scan_path)
            count = len(file_findings)
            label = f"{count} issue{'s' if count != 1 else ''}"

            # File header — keep it with at least the first card
            file_header = [
                Spacer(1, 4 * mm),
                ColoredLine(BORDER_COLOR, thickness=0.3),
                Spacer(1, 3 * mm),
                Table(
                    [[
                        Paragraph(rel, S["filepath"]),
                        Paragraph(label, S["meta"]),
                    ]],
                    colWidths=[usable_w - 40, 40],
                    style=[
                        ("ALIGN",         (1, 0), (1, 0), "RIGHT"),
                        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
                        ("TOPPADDING",    (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                    ],
                ),
            ]

            sorted_findings = sorted(
                file_findings,
                key=lambda x: SEVERITY_ORDER.get(x.get("severity", "LOW"), 3)
            )

            # Keep file header + first card together so headers never orphan
            first_card = _finding_card(sorted_findings[0], S, usable_w)
            story.append(KeepTogether(file_header + [first_card]))

            for f in sorted_findings[1:]:
                story.append(Spacer(1, 3 * mm))
                story.append(_finding_card(f, S, usable_w))

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 10 * mm))
    story.append(ColoredLine(BORDER_COLOR))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Generated by AI Security Scanner · Powered by local Mistral via Ollama · "
        "All analysis ran on your machine · No code was sent to external servers.",
        S["meta"],
    ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return output_path


# Keep old name working too so nothing breaks if someone imported it directly
generate_html_report = generate_report