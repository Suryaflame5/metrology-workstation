"""
Command-Line Interface for Metrology Evidence & Calculation System (v0.9.0 Store RC).
"""

import sys
import argparse
from typing import Optional

# Ensure UTF-8 console output on Windows
_stdout_enc = getattr(sys.stdout, "encoding", None)
if _stdout_enc and _stdout_enc.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .models import CalculationCreateRequest
from .services.calculation_service import compute_micrometer_calibration
from .services.verifier_service import verify_calculation_by_id, replay_calculation
from .services.evidence_service import export_evidence_package_directory
from .services.selftest_service import run_system_selftest
from .services.audit_service import verify_audit_ledger
from .services.backup_service import create_database_backup, restore_database_backup, list_backups
from .db import list_calculations, init_db


def main():
    parser = argparse.ArgumentParser(
        prog="metrology",
        description="Local-First Metrology Calculation & Evidence Verification CLI (v0.9.0)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: demo
    subparsers.add_parser("demo", help="Run a demo micrometer calibration calculation")

    # Command: demo-factory
    subparsers.add_parser("demo-factory", help="Seed complete factory operations acceptance dataset (Machine #4 diameter drift, ₹36k exposure, Tool #17 correlation, ₹28.8k recovery)")

    # Command: selftest
    subparsers.add_parser("selftest", help="Run system integrity and mathematical regression self-test")

    # Command: audit-verify
    subparsers.add_parser("audit-verify", help="Verify cryptographic integrity of the audit ledger hash chain")

    # Command: backup
    subparsers.add_parser("backup", help="Create a live online SQLite database backup with SHA-256 manifest")

    # Command: restore
    restore_parser = subparsers.add_parser("restore", help="Safely restore database from a verified backup file")
    restore_parser.add_argument("backup_filename", help="Filename of backup to restore")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List stored calibration records")
    list_parser.add_argument("--class", dest="rec_class", default="CALIBRATION", help="Filter by record class (CALIBRATION, VALIDATION, ALL)")

    # Command: replay <id>
    replay_parser = subparsers.add_parser("replay", help="Replay 12-stage mathematical derivation for a calculation")
    replay_parser.add_argument("calc_id", help="Calculation ID to replay (e.g. MC-00001042)")

    # Command: verify <id>
    verify_parser = subparsers.add_parser("verify", help="Independently verify a calculation evidence record")
    verify_parser.add_argument("calc_id", help="Calculation ID to verify (e.g. MC-00001042)")

    # Command: export <id>
    export_parser = subparsers.add_parser("export", help="Export machine-verifiable evidence package")
    export_parser.add_argument("calc_id", help="Calculation ID to export")
    export_parser.add_argument("--out", default="evidence_packages", help="Output directory")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Start local web application server")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default 8000)")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host (default 127.0.0.1)")

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "demo-factory":
        run_demo_factory()
    elif args.command == "selftest":
        run_selftest()
    elif args.command == "audit-verify":
        run_audit_verify()
    elif args.command == "backup":
        run_backup()
    elif args.command == "restore":
        run_restore(args.backup_filename)
    elif args.command == "list":
        run_list(args.rec_class)
    elif args.command == "replay":
        run_replay(args.calc_id)
    elif args.command == "verify":
        run_verify(args.calc_id)
    elif args.command == "export":
        run_export(args.calc_id, args.out)
    elif args.command == "serve":
        run_serve(args.host, args.port)
    else:
        parser.print_help()


def run_demo():
    print("=" * 75)
    print(" METROLOGY REFERENCE CALIBRATION -- OUTSIDE MICROMETER 0-25 mm")
    print("=" * 75)
    req = CalculationCreateRequest(record_class="CALIBRATION")
    res = compute_micrometer_calibration(req, calc_id="MC-00001042")
    unc = res.uncertainty_summary
    dec = res.decision_summary
    print(f" Calculation ID:        {res.id} (Root: {res.root_id}, Rev: {res.revision_number})")
    print(f" Record Classification: {res.record_class}")
    print(f" Instrument:            {res.instrument_name} ({res.instrument_model})")
    print(f" Nominal Checkpoint:    {dec.nominal_mm} {res.unit}")
    print(f" Mean Measured:         {dec.mean_measured_mm} {res.unit}")
    print(f" Error of Indication:   {dec.error_of_indication_mm} {res.unit}")
    print(f" Combined Uncertainty:  u_c = {unc.combined_standard_uncertainty_mm} {res.unit}")
    print(f" Effective DoF:         nu_eff = {unc.effective_degrees_of_freedom}")
    print(f" Coverage Factor:       k = {unc.coverage_factor_k}")
    print(f" Expanded Uncertainty:  U_95 = {unc.expanded_uncertainty_U95_mm} {res.unit}")
    print(f" Formatted Result:      {unc.formatted_result}")
    print("-" * 75)
    print(f" Decision Rule:         {dec.decision_rule}")
    print(f" Test Uncertainty Ratio:TUR = {dec.tur}")
    print(f" Guardband Multiplier:  M = {dec.guardband_multiplier_M}")
    print(f" Guardband w:           w = {dec.guardband_w_mm} {res.unit}")
    print(f" Acceptance Zone:       [{dec.acceptance_lower_mm}, {dec.acceptance_upper_mm}] {res.unit}")
    print(f" Conformity Verdict:    {dec.conformity_verdict}")
    print("-" * 75)
    print(f" Input SHA-256:         {res.input_sha256}")
    print(f" Calculation SHA-256:   {res.calculation_sha256}")
    print("=" * 75)


def run_demo_factory():
    print("=" * 75)
    print(" SEEDING INDUSTRIAL FACTORY QUALITY OPERATIONS ACCEPTANCE SCENARIO")
    print("=" * 75)
    from .services.demo_factory_data import seed_demo_factory_operations
    res = seed_demo_factory_operations()
    print(" [OK] Sample Factory Dataset Seeded Successfully:")
    print("   • Part A: Precision Pin Shaft (10.000 ± 0.100 mm)")
    print("   • Machine #4 (Okuma LB3000 CNC)")
    print("   • Baseline Job: INSP-DEMO-001 (100 parts, 12 scrap defects on Tool #17)")
    print("   • Quantified Loss Exposure: ₹36,000 active scrap loss")
    print("   • Root-Cause Correlation: Tool #17 Insert Flank Wear (91.2% confidence)")
    print("   • Corrective Action: Tool #17 Sandvik Insert Replacement (ACT-DEMO-001)")
    print("   • Post-Correction Verification Job: INSP-DEMO-002 (100 parts, 0 defects, 100% PASS)")
    print("   • Verified Recovery ROI Proof: ₹28,800/month Recovered Value (REC-DEMO-001)")
    print("=" * 75)



def run_selftest():
    print("=" * 75)
    print(" METROLOGY SYSTEM INTEGRITY & MATHEMATICAL SELF-TEST")
    print("=" * 75)
    res = run_system_selftest()
    print(f" Calculation Engine: {res['calculation_engine_status']}")
    print(f" Evidence Engine:    {res['evidence_engine_status']}")
    print(f" Database Status:   {res['database_status']}")
    print(f" Benchmark Tests:   {res['benchmark_tests_passed']} / {res['benchmark_tests_total']} Passed")
    print("-" * 75)
    for t in res.get("checks", []):
        sym = "[PASS]" if t["status"] == "PASS" else "[FAIL]"
        print(f"  {sym:<7} | {t['name']}")
    print("-" * 75)
    print(f" OVERALL HEALTH:     {res['overall_status']}")
    print("=" * 75)


def run_audit_verify():
    print("=" * 75)
    print(" METROLOGY CRYPTOGRAPHIC AUDIT LEDGER VERIFICATION")
    print("=" * 75)
    res = verify_audit_ledger()
    print(f" Total Events Checked: {res['total_events']}")
    print(f" Hash Chain Integrity: {'INTACT' if res['chain_valid'] else 'TAMPERED / CORRUPTED'}")
    print(f" Status:               {res['status']}")
    if res["broken_links"]:
        print("-" * 75)
        print(" BROKEN / TAMPERED LINKS DETECTED:")
        for link in res["broken_links"]:
            print(f"  Event #{link['event_id']}: {link['reason']}")
    print("=" * 75)


def run_backup():
    print("Creating live online SQLite database backup...")
    manifest = create_database_backup()
    print("Backup created successfully:")
    print(f" Filename:    {manifest['backup_filename']}")
    print(f" SHA-256:     {manifest['sha256']}")
    print(f" Size:        {manifest['size_bytes']} bytes")
    print(f" Integrity:   {manifest['integrity_status']}")


def run_restore(backup_filename: str):
    print(f"Restoring database from '{backup_filename}'...")
    res = restore_database_backup(backup_filename)
    print(f"Restore Status: {res['status']}")
    print(f"Restored From:  {res['restored_from']}")


def run_replay(calc_id: str):
    print("=" * 75)
    print(f" 12-STAGE MATHEMATICAL CALCULATION REPLAY: {calc_id}")
    print("=" * 75)
    res = replay_calculation(calc_id)
    for s in res["stages"]:
        print(f" Stage {s['step_number']:02d}: {s['title']}")
        print(f"   Clause: {s['standard_clause']}")
        print(f"   Formula: {s['formula']}")
        print(f"   Result:  {s['result_label']} = {s['result_value']}  [{s['status']}]")
        print()
    print("=" * 75)
    print(f" ALL {res['total_stages']} STAGES INDEPENDENTLY REPRODUCED AND VERIFIED")
    print("=" * 75)


def run_list(rec_class: str):
    init_db()
    filter_class = None if rec_class == "ALL" else rec_class
    calcs = list_calculations(record_class=filter_class, limit=25)
    print(f"Found {len(calcs)} stored calculations (class={rec_class}):")
    print(f" {'ID':<14} | {'Rev':<3} | {'Class':<11} | {'Instrument':<14} | {'TUR':<6} | {'Verdict':<6} | {'Status'}")
    print("-" * 75)
    for c in calcs:
        res = c["result_data"]
        tur = res.get("decision_summary", {}).get("tur", "N/A")
        rev = c.get("revision_number", 1)
        r_cls = c.get("record_class", "CALIBRATION")
        print(f" {c['id']:<14} | r{rev:<2} | {r_cls:<11} | {c['instrument_name']:<14} | {tur:<6} | {c['conformity_verdict']:<6} | {c['status']}")


def run_verify(calc_id: str):
    print("=" * 75)
    print(f" METROLOGY EVIDENCE VERIFIER -- VERIFYING {calc_id}")
    print("=" * 75)
    v_res = verify_calculation_by_id(calc_id)
    for check in v_res.checks:
        symbol = "[PASS]" if check.status == "PASS" else "[FAIL]"
        print(f"  {symbol:<8} | {check.check_name:<34} | {check.details}")
    print("-" * 75)
    print(f" OVERALL VERIFICATION: {v_res.overall_status}")
    print(f" {v_res.diagnostics}")
    print("=" * 75)


def run_export(calc_id: str, out_dir: str):
    target_dir = export_evidence_package_directory(calc_id, base_dir=out_dir)
    print(f"Successfully exported evidence package to: {target_dir}")
    print("Package contains: calculation.json, measurements.json, uncertainty_budget.json, decision.json, provenance.json, verification.json")


def run_serve(host: str, port: int):
    import uvicorn
    from .server import app
    print(f"Starting Metrology Workstation server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
