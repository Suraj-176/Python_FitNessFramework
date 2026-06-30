import os
import xml.etree.ElementTree as ET
from datetime import datetime

def find_latest_results_xml():
    results_dir = "FitNesseRoot/files/testResults"
    if not os.path.exists(results_dir):
        return None
        
    latest_file = None
    latest_time = 0
    
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            if file.endswith(".xml"):
                file_path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_file = file_path
                except Exception:
                    continue
                    
    return latest_file

def generate_html_report():
    xml_path = find_latest_results_xml()
    output_html_path = "FitNesseRoot/files/report.html"
    
    if not xml_path:
        # Fallback empty state report if no runs have been executed yet
        write_empty_state_report(output_html_path)
        return
        
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # ── 1. Parse Root Level Summary Data ──
        page_name = root.findtext("rootPath", "Suite Run")
        total_time_ms = int(root.findtext("totalRunTimeInMillis", "0"))
        total_time_s = round(total_time_ms / 1000.0, 3)
        
        # Combined Counts
        final_counts = root.find("finalCounts")
        passed_tests = int(final_counts.findtext("right", "0")) if final_counts is not None else 0
        failed_tests = int(final_counts.findtext("wrong", "0")) if final_counts is not None else 0
        ignored_tests = int(final_counts.findtext("ignores", "0")) if final_counts is not None else 0
        exceptions_tests = int(final_counts.findtext("exceptions", "0")) if final_counts is not None else 0
        
        total_tests = passed_tests + failed_tests + ignored_tests + exceptions_tests
        
        # Calculate percentages for the Branded Pie/Ring Chart
        pass_pct = round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0
        fail_pct = round(((failed_tests + exceptions_tests) / total_tests) * 100, 1) if total_tests > 0 else 0
        
        # Get Timestamp from XML filename or file mtime
        file_time = os.path.getmtime(xml_path)
        run_date = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %I:%M:%S %p')
        
        # ── 2. Parse Individual Test Case Results ──
        test_cases_html = ""
        results = root.findall(".//result")
        
        for idx, res in enumerate(results):
            tc_name = res.findtext("relativePageName", "Test Case")
            tc_time_ms = int(res.findtext("totalRunTimeInMillis", "0"))
            tc_time_s = round(tc_time_ms / 1000.0, 3)
            
            # Individual Counts
            counts = res.find("counts")
            tc_right = int(counts.findtext("right", "0")) if counts is not None else 0
            tc_wrong = int(counts.findtext("wrong", "0")) if counts is not None else 0
            tc_ignores = int(counts.findtext("ignores", "0")) if counts is not None else 0
            tc_exceptions = int(counts.findtext("exceptions", "0")) if counts is not None else 0
            
            # Status Badge Class
            if tc_wrong > 0 or tc_exceptions > 0:
                status_class = "fail"
                status_text = "❌ FAILED"
            else:
                status_class = "pass"
                status_text = "✔ PASSED"
                
            # Parse execution log stdout/stderr if available
            std_err = res.findtext(".//stdErr", "")
            std_out = res.findtext(".//stdOut", "")
            logs = (std_err + "\n" + std_out).strip()
            
            log_div_html = ""
            if logs:
                # Limit size
                truncated_logs = logs[:3000] + "..." if len(logs) > 3000 else logs
                log_div_html = f"""
                <div class="tc-logs-toggle" onclick="toggleLogs({idx})">Toggle Execution Logs (Stdout/Stderr) 🔍</div>
                <div id="logs-{idx}" class="tc-logs-block" style="display: none;">
                    <pre>{truncated_logs}</pre>
                </div>"""
                
            test_cases_html += f"""
            <div class="tc-card">
                <div class="tc-header">
                    <div class="tc-title">
                        <span class="tc-bullet">•</span>
                        <strong>{tc_name}</strong>
                    </div>
                    <div class="tc-badge {status_class}">{status_text}</div>
                </div>
                <div class="tc-meta">
                    Duration: <strong>{tc_time_s}s</strong> &nbsp;|&nbsp; 
                    Assertions: <span class="lbl pass">Right: {tc_right}</span> 
                    <span class="lbl fail">Wrong: {tc_wrong}</span> 
                    <span class="lbl err">Exceptions: {tc_exceptions}</span>
                </div>
                {log_div_html}
            </div>"""
            
        # ── 3. Build Branded HTML Dashboard ──
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ICICI Prudential AML &mdash; 3rd Party API Quality Report</title>
    <style>
        :root {{
            --primary: #A6192E;
            --secondary: #004A80;
            --orange: #E06336;
            --bg: #f8fafc;
            --text-main: #1e293b;
            --text-muted: #64748b;
        }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            margin: 0; padding: 40px 20px;
        }}
        .container {{
            max-width: 950px;
            margin: 0 auto;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-top: 6px solid var(--primary);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, #7E1322 40%, var(--secondary) 100%);
            padding: 36px 40px;
            color: #fff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 4px solid var(--orange);
        }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
        .header p {{ margin: 5px 0 0; font-size: 13px; color: rgba(255,255,255,0.8); letter-spacing: 0.5px; text-transform: uppercase; }}
        
        .export-btn {{
            padding: 8px 16px;
            background: var(--orange);
            color: #fff;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.18s;
            text-transform: uppercase;
        }}
        .export-btn:hover {{ background: #c0441a; }}
        
        .summary-section {{
            display: flex;
            padding: 40px;
            gap: 40px;
            border-bottom: 1px dashed #e2e8f0;
            align-items: center;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            flex: 1;
        }}
        .stat-card {{
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .stat-card h4 {{ margin: 0 0 6px; font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; }}
        .stat-card p {{ margin: 0; font-size: 24px; font-weight: 700; color: var(--text-main); }}
        .stat-card.pass p {{ color: #15803d; }}
        .stat-card.fail p {{ color: #b91c1c; }}
        
        /* Branded Pie Ring Chart CSS */
        .chart-box {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 180px;
        }}
        .radial-chart {{
            width: 130px; height: 130px;
            border-radius: 50%;
            background: conic-gradient(#15803d 0% {pass_pct}%, #b91c1c {pass_pct}% 100%);
            display: flex; align-items: center; justify-content: center;
            position: relative;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
        }}
        .radial-chart::after {{
            content: '';
            position: absolute;
            width: 90px; height: 90px;
            background: #fff;
            border-radius: 50%;
        }}
        .chart-value {{
            position: relative;
            z-index: 10;
            font-size: 22px;
            font-weight: 700;
            color: var(--text-main);
        }}
        .chart-label {{
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            margin-top: 8px;
            text-transform: uppercase;
        }}
        
        .results-section {{ padding: 40px; }}
        .section-title {{
            font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;
            color: var(--primary); margin: 0 0 20px; display: flex; align-items: center; gap: 8px;
        }}
        .section-title::after {{
            content: ''; flex: 1; height: 2px;
            background: linear-gradient(90deg, var(--orange), transparent);
        }}
        
        .tc-card {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            background: #fff;
            transition: box-shadow 0.18s;
        }}
        .tc-card:hover {{ box-shadow: 0 3px 10px rgba(0,0,0,0.04); }}
        .tc-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .tc-title {{ display: flex; align-items: center; gap: 8px; font-size: 15px; color: var(--text-main); }}
        .tc-bullet {{ color: var(--secondary); font-size: 20px; line-height: 1; }}
        
        .tc-badge {{
            padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.3px;
        }}
        .tc-badge.pass {{ background: #dcfce7; color: #15803d; }}
        .tc-badge.fail {{ background: #fee2e2; color: #b91c1c; }}
        
        .tc-meta {{ font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-bottom: 10px; }}
        .tc-meta .lbl {{ font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-left: 4px; }}
        .tc-meta .lbl.pass {{ background: #f0fdf4; color: #166534; }}
        .tc-meta .lbl.fail {{ background: #fef2f2; color: #991b1b; }}
        .tc-meta .lbl.err {{ background: #fffbeb; color: #9a3412; }}
        
        .tc-logs-toggle {{
            font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--secondary);
            cursor: pointer; display: inline-block; margin-top: 6px; user-select: none;
        }}
        .tc-logs-toggle:hover {{ text-decoration: underline; }}
        .tc-logs-block {{
            background: #0f172a; color: #38bdf8; padding: 16px; border-radius: 6px;
            margin-top: 10px; overflow-x: auto; box-shadow: inset 0 2px 8px rgba(0,0,0,0.25);
        }}
        .tc-logs-block pre {{ margin: 0; font-family: 'Consolas', monospace; font-size: 12px; line-height: 1.5; }}
        
        /* Printing Layout Overrides */
        @media print {{
            body {{ background: #fff; padding: 0; }}
            .container {{ box-shadow: none; border-top: none; max-width: 100%; }}
            .export-btn {{ display: none; }}
            .tc-logs-toggle, .tc-logs-block {{ display: none !important; }}
            .tc-card {{ page-break-inside: avoid; }}
        }}
    </style>
    <script>
        function toggleLogs(idx) {{
            var block = document.getElementById("logs-" + idx);
            if (block) {{
                block.style.display = block.style.display === "none" ? "block" : "none";
            }}
        }}
    </script>
</head>
<body>

<div class="container">
    
    <!-- Header -->
    <div class="header">
        <div>
            <h1>ICICI Prudential Branded Quality Report</h1>
            <p>Suite Name: {page_name} &nbsp;|&nbsp; Executed: {run_date}</p>
        </div>
        <button class="export-btn" onclick="window.print()">💾 Save PDF Report</button>
    </div>
    
    <!-- Summary Stats section -->
    <div class="summary-section">
        
        <div class="stats-grid">
            <div class="stat-card">
                <h4>Total Run Duration</h4>
                <p>{total_time_s}s</p>
            </div>
            <div class="stat-card">
                <h4>Total Test Cases</h4>
                <p>{total_tests}</p>
            </div>
            <div class="stat-card pass">
                <h4>Passed Cases</h4>
                <p>{passed_tests}</p>
            </div>
            <div class="stat-card fail">
                <h4>Failed / Errors</h4>
                <p>{failed_tests + exceptions_tests}</p>
            </div>
        </div>
        
        <!-- Pie Ring Chart -->
        <div class="chart-box">
            <div class="radial-chart">
                <span class="chart-value">{pass_pct}%</span>
            </div>
            <span class="chart-label">Pass Percentage</span>
        </div>
        
    </div>
    
    <!-- Results section -->
    <div class="results-section">
        <div class="section-title">📊 Execution Results Grid</div>
        {test_cases_html}
    </div>

</div>

</body>
</html>
"""
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[3RD PARTY REPORT GENERATED] {output_html_path}")
        
    except Exception as e:
        print(f"[ERROR] Failed to generate 3rd party report: {str(e)}")

def write_empty_state_report(path):
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ICICI Prudential Quality Report — Empty State</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f8fafc; text-align: center; padding: 80px 20px; }
        .box { background: #fff; border-radius: 8px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); max-width: 500px; margin: 0 auto; border-top: 4px solid #A6192E; }
        h2 { color: #A6192E; margin: 0 0 10px; }
        p { color: #64748b; font-size: 14px; line-height: 1.6; margin-bottom: 20px; }
    </style>
</head>
<body>
<div class="box">
    <h2>No Executions Found</h2>
    <p>We couldn't find any previous test runs inside your workspace yet. Please run your tests or suites first, and refresh this page to view your gorgeous corporate quality reports!</p>
</div>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_html_report()
