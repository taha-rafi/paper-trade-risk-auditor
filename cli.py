"""
Paper Trade Risk Auditor - Unified CLI Workflow
Enables single-command CSV ingestion, deterministic risk calculation, and HTML/JSON report generation.
"""
import argparse
import sys
import os
import json

# Ensure core package is importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.csv_loader import parse_trades_csv
from core.auditor import RiskAuditor
from core.html_reporter import generate_html_report

def main():
    parser = argparse.ArgumentParser(
        description="Paper Trade Risk Auditor - Ingest CSV trade history and generate risk audit reports."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Audit a trade history CSV file")
    audit_parser.add_argument("csv_file", help="Path to trade ledger CSV file")
    audit_parser.add_argument("--equity", type=float, default=10000.0, help="Initial account equity in USD (default: 10000.0)")
    audit_parser.add_argument("--html", type=str, default="audit_report.html", help="Output path for standalone HTML report")
    audit_parser.add_argument("--json", type=str, default=None, help="Output path for raw JSON report")
    audit_parser.add_argument("--title", type=str, default="Trade History Risk Audit Report", help="Report header title")

    args = parser.parse_args()

    if args.command == "audit":
        print(f"[*] Ingesting CSV trade ledger from: {args.csv_file}")
        trades, errors = parse_trades_csv(args.csv_file)

        if errors:
            print(f"[!] Validation Warnings/Errors ({len(errors)}):")
            for err in errors:
                print(f"    - {err}")
            if not trades:
                print("[-] Fatal: No valid trade records parsed. Aborting audit.")
                sys.exit(1)

        print(f"[+] Successfully validated {len(trades)} trade records.")
        print(f"[*] Running FIFO cost-basis audit with initial equity of ${args.equity:,.2f}...")

        auditor = RiskAuditor(initial_equity=args.equity)
        report = auditor.audit(trades)

        print("\n" + "="*50)
        print("          AUDIT EXECUTIVE SUMMARY")
        print("="*50)
        print(f"Total Trades Audited:        {report.total_trades}")
        print(f"Initial Equity:              ${report.initial_equity:,.2f}")
        print(f"Final Equity:                ${report.final_equity:,.2f}")
        print(f"Net Realized PnL:            ${report.realized_net_pnl:,.2f}")
        print(f"Total Execution Fees:        ${report.total_fees:,.2f}")
        print(f"Win Rate:                    {report.win_rate_pct:.1f}% ({report.winning_trades}W / {report.losing_trades}L)")
        print(f"Profit Factor:               {report.profit_factor if report.profit_factor != float('inf') else 'Infinity'}")
        print(f"Max Drawdown:                {report.max_drawdown_pct:.2f}% (${report.max_drawdown_usd:,.2f})")
        print(f"Max Single-Asset Exposure:   {report.max_exposure_concentration_pct:.1f}%")
        print(f"Integrity Flags Detected:    {len(report.invalid_position_flags)}")
        for flag in report.invalid_position_flags:
            print(f"  [!] {flag}")
        print("="*50 + "\n")

        # HTML Export
        if args.html:
            html_content = generate_html_report(report, trades=trades, title=args.title)
            with open(args.html, "w", encoding="utf-8") as hf:
                hf.write(html_content)
            print(f"[+] Standalone HTML report generated: {os.path.abspath(args.html)}")

        # JSON Export
        if args.json:
            with open(args.json, "w", encoding="utf-8") as jf:
                json.dump(report.to_dict(), jf, indent=2)
            print(f"[+] Raw JSON metrics exported: {os.path.abspath(args.json)}")

        print("[+] Audit completed successfully.")

if __name__ == "__main__":
    main()
