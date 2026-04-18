"""
main.py — AI Security Scanner entry point
==========================================
Usage:
  python main.py ./path/to/project
  python main.py ./path/to/project --output my-report.html

To switch AI provider, edit config.py — no other file needs to change.
"""

import sys
import os
import argparse
from datetime import datetime

from scanner import walk_codebase, get_file_stats
from scanner.stripper import process_files
from scanner.analyzer import analyze_codebase
from scanner.reporter import generate_html_report
import config


def main():
    parser = argparse.ArgumentParser(
        description="AI Security Scanner — finds vulnerabilities in your codebase"
    )
    parser.add_argument(
        "path",
        help="Path to the project folder you want to scan"
    )
    parser.add_argument(
        "--output", default=None,
        help="Custom path for the HTML report (optional)"
    )
    args = parser.parse_args()

    scan_path = os.path.abspath(args.path)

    if not os.path.exists(scan_path):
        print(f"\n[ERROR] Folder not found: {scan_path}")
        sys.exit(1)

    model_label = getattr(config, config.PROVIDER.upper() + "_MODEL", "unknown")

    print(f"\n{'='*55}")
    print(f"  AI Security Scanner")
    print(f"{'='*55}")
    print(f"  Target   : {scan_path}")
    print(f"  Provider : {config.PROVIDER}  ({model_label})")
    print(f"{'='*55}\n")

    # Step 1 — Walk
    print("Step 1/4  Walking codebase...")
    files = walk_codebase(scan_path)
    stats = get_file_stats(files, scan_path)
    print(f"          Found {stats['total_files']} files "
          f"({stats['total_lines']:,} lines)\n")

    if not files:
        print("[!] No scannable files found. Exiting.")
        sys.exit(0)

    # Step 2 — Strip secrets
    print("Step 2/4  Stripping secrets...")
    processed = process_files(files)
    print()

    # Step 3 — Analyze
    print("Step 3/4  Running AI analysis...")
    findings = analyze_codebase(processed)

    # Step 4 — Report
    print("\nStep 4/4  Generating report...")
    timestamp   = datetime.now().strftime("%Y-%m-%d_%H-%M")
    report_name = f"scan_{timestamp}.html"
    output_path = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        config.REPORTS_DIR,
        report_name,
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generate_html_report(findings, scan_path, stats, output_path)

    print(f"\n{'='*55}")
    print(f"  Scan complete!")
    print(f"  Issues found : {len(findings)}")
    print(f"  Report saved : {output_path}")
    print(f"{'='*55}")
    print(f"\n  Open your report:")
    print(f"  open \"{output_path}\"\n")


if __name__ == "__main__":
    main()