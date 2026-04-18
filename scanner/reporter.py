import os
import json
from datetime import datetime

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

SEVERITY_COLORS = {
    "CRITICAL": "#e24b4a",
    "HIGH":     "#ef9f27",
    "MEDIUM":   "#378add",
    "LOW":      "#639922",
}

SEVERITY_BG = {
    "CRITICAL": "#fcebeb",
    "HIGH":     "#faeeda",
    "MEDIUM":   "#e6f1fb",
    "LOW":      "#eaf3de",
}


def group_by_file(findings):
    grouped = {}
    for f in findings:
        path = f.get("file", "unknown")
        grouped.setdefault(path, []).append(f)
    return grouped


def severity_badge(severity):
    color  = SEVERITY_COLORS.get(severity, "#888")
    bg     = SEVERITY_BG.get(severity, "#eee")
    return (f'<span style="background:{bg};color:{color};'
            f'font-weight:500;padding:2px 10px;border-radius:20px;'
            f'font-size:12px;border:1px solid {color}33">{severity}</span>')


def summary_counts(findings):
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        s = f.get("severity", "LOW")
        counts[s] = counts.get(s, 0) + 1
    return counts


def render_finding(f):
    severity = f.get("severity", "LOW")
    border   = SEVERITY_COLORS.get(severity, "#ccc")
    return f"""
    <div style="border-left:4px solid {border};padding:16px 20px;
                margin-bottom:12px;background:var(--card);
                border-radius:0 8px 8px 0">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        {severity_badge(severity)}
        <span style="font-weight:500;font-size:15px">{f.get("type","Unknown")}</span>
        <span style="margin-left:auto;font-size:12px;
                     color:#888">Line {f.get("line","?")}</span>
      </div>
      <p style="margin:4px 0;font-size:14px">
        <span style="color:#888">What:</span> {f.get("description","")}
      </p>
      <p style="margin:4px 0;font-size:14px">
        <span style="color:#888">Risk:</span> {f.get("risk","")}
      </p>
      <div style="margin-top:10px;background:#f6f8fa;border-radius:6px;
                  padding:10px 14px;font-size:13px;border:1px solid #e0e0e0">
        <span style="color:#3b6d11;font-weight:500">Fix: </span>
        {f.get("fix","")}
      </div>
    </div>"""


def render_file_section(filepath, findings, root_path):
    sorted_findings = sorted(
        findings,
        key=lambda x: SEVERITY_ORDER.get(x.get("severity", "LOW"), 3)
    )
    rel_path = os.path.relpath(filepath, root_path) if root_path else filepath
    cards    = "".join(render_finding(f) for f in sorted_findings)
    count    = len(findings)
    label    = f"{count} issue{'s' if count != 1 else ''}"

    return f"""
    <div style="margin-bottom:28px">
      <div style="display:flex;align-items:center;gap:10px;
                  margin-bottom:10px;padding-bottom:8px;
                  border-bottom:1px solid var(--border)">
        <code style="font-size:14px;font-weight:500">{rel_path}</code>
        <span style="font-size:12px;color:#888;margin-left:auto">{label}</span>
      </div>
      {cards}
    </div>"""


def generate_html_report(findings, scan_path, stats, output_path):
    """
    Generates a full HTML report and saves it to output_path.
    findings   : list of finding dicts from analyzer
    scan_path  : the root path that was scanned
    stats      : dict from walker.get_file_stats()
    output_path: where to save the .html file
    """
    counts      = summary_counts(findings)
    grouped     = group_by_file(findings)
    total       = len(findings)
    scanned_at  = datetime.now().strftime("%B %d, %Y at %H:%M")
    project     = os.path.basename(os.path.abspath(scan_path))

    # Sort files — files with critical issues first
    def file_priority(item):
        path, file_findings = item
        severities = [f.get("severity","LOW") for f in file_findings]
        return min(SEVERITY_ORDER.get(s, 3) for s in severities)

    sorted_files = sorted(grouped.items(), key=file_priority)
    file_sections = "".join(
        render_file_section(path, file_findings, scan_path)
        for path, file_findings in sorted_files
    )

    # Summary bar cards
    def summary_card(label, count, color, bg):
        return f"""
        <div style="flex:1;min-width:120px;background:{bg};border:1px solid {color}33;
                    border-radius:10px;padding:16px 20px;text-align:center">
          <div style="font-size:28px;font-weight:500;color:{color}">{count}</div>
          <div style="font-size:12px;color:{color};margin-top:2px">{label}</div>
        </div>"""

    summary_html = "".join([
        summary_card("CRITICAL", counts["CRITICAL"],
                     SEVERITY_COLORS["CRITICAL"], SEVERITY_BG["CRITICAL"]),
        summary_card("HIGH",     counts["HIGH"],
                     SEVERITY_COLORS["HIGH"],     SEVERITY_BG["HIGH"]),
        summary_card("MEDIUM",   counts["MEDIUM"],
                     SEVERITY_COLORS["MEDIUM"],   SEVERITY_BG["MEDIUM"]),
        summary_card("LOW",      counts["LOW"],
                     SEVERITY_COLORS["LOW"],      SEVERITY_BG["LOW"]),
    ])

    no_issues_html = ""
    if total == 0:
        no_issues_html = """
        <div style="text-align:center;padding:60px 20px;color:#639922">
          <div style="font-size:48px">✓</div>
          <div style="font-size:18px;font-weight:500;margin-top:12px">
            No vulnerabilities found
          </div>
          <div style="font-size:14px;color:#888;margin-top:6px">
            The scanned files look clean.
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Security Scan — {project}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f5f0; color: #1a1a1a; line-height: 1.6;
    }}
    :root {{ --card: #ffffff; --border: #e8e8e0; }}
    .container {{ max-width: 860px; margin: 0 auto; padding: 32px 20px; }}
    h1 {{ font-size: 22px; font-weight: 500; }}
    h2 {{ font-size: 16px; font-weight: 500; margin-bottom: 16px; color: #444; }}
    a {{ color: inherit; text-decoration: none; }}
  </style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div style="margin-bottom:28px">
    <h1>Security scan report</h1>
    <div style="font-size:13px;color:#888;margin-top:4px">
      Project: <strong>{project}</strong> &nbsp;·&nbsp;
      Scanned: {scanned_at} &nbsp;·&nbsp;
      Files: {stats.get("total_files", 0)} &nbsp;·&nbsp;
      Lines: {stats.get("total_lines", 0):,}
    </div>
  </div>

  <!-- Summary cards -->
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:32px">
    {summary_html}
  </div>

  <!-- Findings -->
  <div style="background:var(--card);border:1px solid var(--border);
              border-radius:12px;padding:24px">
    <h2>Findings — {total} total</h2>
    {file_sections if total > 0 else no_issues_html}
  </div>

  <!-- Footer -->
  <div style="margin-top:20px;font-size:12px;color:#aaa;text-align:center">
    Generated by AI Security Scanner · Powered by Mistral (local)
  </div>

</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(html)

    return output_path