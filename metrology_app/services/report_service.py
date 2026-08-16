"""
Report Service: Generates clean, human-readable calibration certificate & evidence reports.
"""

from typing import Dict, Any
from ..db import get_calculation
from .. import __version__ as APP_VERSION


def generate_html_report(calc_id: str) -> str:
    """Generate a clean, standalone, printable HTML calibration certificate report."""
    calc_data = get_calculation(calc_id)
    if not calc_data:
        raise ValueError(f"Calculation '{calc_id}' not found")

    res = calc_data["result_data"]
    inp = calc_data["input_data"]
    unc = res.get("uncertainty_summary", {})
    dec = res.get("decision_summary", {})
    verdict = calc_data["conformity_verdict"]

    verdict_badge_color = "#10b981" if verdict == "PASS" else ("#f59e0b" if verdict == "GUARD_BAND" else "#ef4444")

    # Table rows HTML
    rows_html = ""
    for r in unc.get("budget_rows", []):
        rows_html += f"""
        <tr>
            <td style="font-weight: 500;">{r['label']}</td>
            <td style="text-align: center;">{r['component_type']}</td>
            <td>{r['distribution']}</td>
            <td style="text-align: center;">{r['divisor']}</td>
            <td style="text-align: right; font-family: monospace;">{r['standard_uncertainty_mm']}</td>
            <td style="text-align: center;">{r['sensitivity_coefficient']}</td>
            <td style="text-align: right; font-family: monospace;">{r['percentage_contribution']}</td>
            <td style="text-align: center;">{r['degrees_of_freedom']}</td>
        </tr>
        """

    # Measurements HTML
    obs = inp.get("repeatability", {}).get("measurements", [])
    obs_html = ", ".join([f"{x:.4f} mm" for x in obs])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Calibration Certificate — {calc_id}</title>
    <style>
        @page {{ size: A4; margin: 15mm; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
            line-height: 1.5;
            background: #fff;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0f172a;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .title h1 {{ margin: 0; font-size: 24px; color: #0f172a; letter-spacing: -0.5px; }}
        .title p {{ margin: 4px 0 0 0; color: #64748b; font-size: 13px; }}
        .meta-box {{ text-align: right; font-size: 12px; }}
        .meta-box span {{ display: block; }}
        .id-badge {{
            font-family: monospace;
            background: #f1f5f9;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 13px;
        }}
        .section-title {{
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #334155;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 5px;
            margin-top: 25px;
            margin-bottom: 12px;
        }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .info-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px 16px;
            font-size: 13px;
        }}
        .info-row {{ display: flex; justify-content: space-between; margin-bottom: 6px; }}
        .info-label {{ color: #64748b; font-weight: 500; }}
        .info-val {{ font-weight: 600; color: #0f172a; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 10px;
        }}
        th {{
            background: #f1f5f9;
            color: #475569;
            font-weight: 600;
            text-align: left;
            padding: 8px 10px;
            border: 1px solid #cbd5e1;
        }}
        td {{
            padding: 7px 10px;
            border: 1px solid #e2e8f0;
        }}
        .verdict-banner {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #f8fafc;
            border: 2px solid {verdict_badge_color};
            border-radius: 8px;
            padding: 16px 20px;
            margin-top: 20px;
        }}
        .verdict-tag {{
            background: {verdict_badge_color};
            color: white;
            padding: 6px 18px;
            border-radius: 4px;
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 1px;
        }}
        .provenance-box {{
            background: #0f172a;
            color: #f8fafc;
            border-radius: 6px;
            padding: 14px 18px;
            font-size: 11px;
            margin-top: 25px;
            font-family: monospace;
        }}
        .hash-line {{ word-break: break-all; margin-top: 4px; color: #38bdf8; }}
        .print-btn {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            float: right;
            margin-bottom: 10px;
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Print / Save PDF</button>

    <div class="header">
        <div class="title">
            <h1>Measurement Uncertainty & Calibration Certificate</h1>
            <p>Conforming to JCGM 100:2008 (GUM), JCGM 106:2012, and ANSI/NCSL Z540.3</p>
        </div>
        <div class="meta-box">
            <span class="id-badge">{calc_id}</span>
            <span style="margin-top: 5px; color: #64748b;">Issued: {calc_data['created_at'][:19]}Z</span>
            <span style="color: #64748b;">Engine: metrology-core 0.3.0</span>
        </div>
    </div>

    <div class="grid-2">
        <div class="info-card">
            <div class="info-row"><span class="info-label">Instrument:</span><span class="info-val">{calc_data['instrument_name']}</span></div>
            <div class="info-row"><span class="info-label">Model / Range:</span><span class="info-val">{calc_data['instrument_model']}</span></div>
            <div class="info-row"><span class="info-label">Procedure:</span><span class="info-val">{calc_data['procedure_name']} (v{calc_data['procedure_version']})</span></div>
            <div class="info-row"><span class="info-label">Nominal Checkpoint:</span><span class="info-val">{dec.get('nominal_mm')} mm</span></div>
        </div>
        <div class="info-card">
            <div class="info-row"><span class="info-label">Decision Rule:</span><span class="info-val">{calc_data['decision_rule']}</span></div>
            <div class="info-row"><span class="info-label">Tolerance Limits:</span><span class="info-val">[{dec.get('tolerance_lower_mm')}, {dec.get('tolerance_upper_mm')}] mm</span></div>
            <div class="info-row"><span class="info-label">Confidence Level:</span><span class="info-val">{calc_data['confidence_level']} (k = {unc.get('coverage_factor_k')})</span></div>
            <div class="info-row"><span class="info-label">Test Uncertainty Ratio:</span><span class="info-val">TUR = {dec.get('tur')}</span></div>
        </div>
    </div>

    <div class="section-title">1. Measurement Data & Observations</div>
    <div style="font-size: 13px; background: #f8fafc; padding: 10px 15px; border-radius: 4px; border: 1px solid #e2e8f0;">
        <strong>Repeated Readings (5 trials):</strong> {obs_html}<br>
        <strong>Mean Measured Value:</strong> {dec.get('mean_measured_mm')} mm &nbsp;|&nbsp; 
        <strong>Error of Indication (&Delta;x):</strong> {dec.get('error_of_indication_mm')} mm
    </div>

    <div class="section-title">2. GUM Uncertainty Budget Table</div>
    <table>
        <thead>
            <tr>
                <th>Uncertainty Source</th>
                <th style="text-align: center;">Type</th>
                <th>Distribution</th>
                <th style="text-align: center;">Divisor</th>
                <th style="text-align: right;">Std Uncertainty (mm)</th>
                <th style="text-align: center;">c<sub>i</sub></th>
                <th style="text-align: right;">Contribution</th>
                <th style="text-align: center;">&nu;<sub>i</sub></th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div style="margin-top: 15px; font-size: 13px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; text-align: center;">
        <div style="background: #f1f5f9; padding: 8px; border-radius: 4px;">
            <div style="color: #64748b; font-size: 11px;">Combined u<sub>c</sub></div>
            <div style="font-weight: 700; font-family: monospace;">{unc.get('combined_standard_uncertainty_mm')} mm</div>
        </div>
        <div style="background: #f1f5f9; padding: 8px; border-radius: 4px;">
            <div style="color: #64748b; font-size: 11px;">Effective DoF &nu;<sub>eff</sub></div>
            <div style="font-weight: 700; font-family: monospace;">{unc.get('effective_degrees_of_freedom')}</div>
        </div>
        <div style="background: #f1f5f9; padding: 8px; border-radius: 4px;">
            <div style="color: #64748b; font-size: 11px;">Coverage Factor k</div>
            <div style="font-weight: 700; font-family: monospace;">{unc.get('coverage_factor_k')}</div>
        </div>
        <div style="background: #e0f2fe; padding: 8px; border-radius: 4px; border: 1px solid #bae6fd;">
            <div style="color: #0369a1; font-size: 11px; font-weight: 600;">Expanded U<sub>95</sub></div>
            <div style="font-weight: 800; font-family: monospace; color: #0284c7;">{unc.get('expanded_uncertainty_U95_mm')} mm</div>
        </div>
    </div>

    <div class="section-title">3. Conformity Assessment & Decision Rule</div>
    <div class="verdict-banner">
        <div>
            <div style="font-size: 14px; font-weight: 700; color: #0f172a;">Conformity Assessment Result</div>
            <div style="font-size: 12px; color: #475569; margin-top: 2px;">
                Measured Error: <strong>{dec.get('error_of_indication_mm')} mm</strong> inside Acceptance Zone 
                <strong>[{dec.get('acceptance_lower_mm')}, {dec.get('acceptance_upper_mm')}] mm</strong> 
                (Guardband w = {dec.get('guardband_w_mm')} mm)
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
                {dec.get('decision_explanation')}
            </div>
        </div>
        <div class="verdict-tag">{verdict}</div>
    </div>

    <div class="provenance-box">
        <div><strong>CRYPTOGRAPHIC PROVENANCE &amp; TAMPER-EVIDENT RECORD</strong></div>
        <div>Input SHA-256 Digest:</div>
        <div class="hash-line">{calc_data['input_sha256']}</div>
        <div style="margin-top: 6px;">Calculation SHA-256 Digest:</div>
        <div class="hash-line">{calc_data['calculation_sha256']}</div>
        <div style="margin-top: 8px; color: #94a3b8; font-size: 10px;">
            Independent Verification: <code>python -m metrology_app.cli verify {calc_id}</code>
        </div>
    </div>
</body>
</html>
"""
    return html
