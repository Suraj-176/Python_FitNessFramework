"""Small local file-backed user store for the FitNesse UI demo."""
import html
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

USERS_FILE = os.path.join(BASE_DIR, "data", "users.json")
FITNESSE_USERS_FILE = os.path.join(BASE_DIR, "runtime", "fitnesse-passwords.txt")
HOST = "0.0.0.0"
PORT = 8090

# Memory-only Queue to dynamically source FitNesse page names with ZERO table modifications!
ACTIVE_RUNS_QUEUE = []


def read_users():
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def write_users(users):
    temporary_file = USERS_FILE + ".tmp"
    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=2)
        file.write("\n")
    os.replace(temporary_file, USERS_FILE)


def sync_fitnesse_password_file(users=None):
    """Generate FitNesse's temporary username:password adapter from JSON."""
    users = users or read_users()
    os.makedirs(os.path.dirname(FITNESSE_USERS_FILE), exist_ok=True)
    temporary_file = FITNESSE_USERS_FILE + ".tmp"
    with open(temporary_file, "w", encoding="utf-8") as file:
        for username, user in sorted(users.items()):
            file.write(f"{username}:{user['password']}\n")
    os.replace(temporary_file, FITNESSE_USERS_FILE)


def update_env_file(payload):
    """
    Dynamically parses the local .env file.
    Preserves all framework-level configurations intact.
    Completely synchronizes and mirrors environment-wise URLs on disk
    to match exactly what the user added, edited, or deleted in the UI.
    """
    env_file = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_file):
        env_file = os.path.join(BASE_DIR, ".env.example")
        if not os.path.exists(env_file):
            return
            
    with open(env_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    environments = payload.get("environments", {})
    runtime_config = payload.get("config", {})
    
    preserved_lines = []
    
    # 1. Process and filter existing .env lines
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            # Strip out older dynamic sync comments or section headers to avoid duplicates
            if "DYNAMICALLY SYNCHRONIZED" not in line_stripped and "from UI" not in line_stripped:
                preserved_lines.append(line)
            continue
            
        if "=" in line_stripped:
            key, val = line_stripped.split("=", 1)
            key = key.strip()
            
            # Check if this key is an environment-wise URL
            is_env_url = False
            if key.endswith("_API_URL") or key.endswith("_BASE_URL") or key.endswith("_UI_URL") or (key.endswith("_URL") and "UI" not in key and "TOKEN" not in key):
                is_env_url = True
                
            if is_env_url:
                continue  # Discard old environment-specific URL lines completely!
                
            # Update runtime configs on the fly if present in payload
            if key == "UI_BROWSER" and "browser" in runtime_config:
                preserved_lines.append(f"UI_BROWSER={runtime_config['browser']}\n")
            elif key == "UI_HEADLESS" and "headless" in runtime_config:
                preserved_lines.append(f"UI_HEADLESS={runtime_config['headless']}\n")
            elif key == "MAX_RETRIES" and "retries" in runtime_config:
                preserved_lines.append(f"MAX_RETRIES={runtime_config['retries']}\n")
            elif key == "RETRY_DELAY" and "delay" in runtime_config:
                preserved_lines.append(f"RETRY_DELAY={runtime_config['delay']}\n")
            elif key == "UI_WORKERS" and "workers" in runtime_config:
                preserved_lines.append(f"UI_WORKERS={runtime_config['workers']}\n")
            else:
                preserved_lines.append(line)
        else:
            preserved_lines.append(line)
            
    # 2. Compile exactly the active environments list from the UI
    new_env_lines = []
    new_env_lines.append("\n# ═════════════════════════════════════════════════════════════════════\n")
    new_env_lines.append("# DYNAMICALLY SYNCHRONIZED ENVIRONMENTS FROM THE UI\n")
    new_env_lines.append("# ═════════════════════════════════════════════════════════════════════\n")
    
    for env_name, urls in sorted(environments.items()):
        env_upper = env_name.upper().replace(" ", "_")
        api_url = urls.get("api", "").strip()
        ui_url = urls.get("ui", "").strip()
        
        new_env_lines.append(f"{env_upper}_API_URL={api_url}\n")
        new_env_lines.append(f"{env_upper}_UI_URL={ui_url}\n")
        
    final_lines = preserved_lines + new_env_lines
    
    # 3. Write mirrored results straight to disk
    temporary_file = env_file + ".tmp"
    with open(temporary_file, "w", encoding="utf-8") as f:
        f.writelines(final_lines)
    os.replace(temporary_file, env_file)


class UserStoreHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(204, {})

    def do_GET(self):
        if self.path == "/users":
            try:
                self._send_json(200, read_users())
            except (OSError, json.JSONDecodeError) as error:
                self._send_json(500, {"error": str(error)})
            return
            
        elif self.path == "/serve-allure":
            try:
                import subprocess
                import shutil
                results_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "testResults", "allure-results")
                report_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "testResults", "allure-report")
                os.makedirs(results_path, exist_ok=True)
                
                # Write Environment Metadata to populate the Allure Environment widget!
                env_path = os.path.join(results_path, "environment.properties")
                with open(env_path, "w", encoding="utf-8") as ef:
                    ef.write("Browser=Chromium (Playwright)\n")
                    ef.write("Headless=Headed (Live Debug Supported)\n")
                    ef.write("Platform=Windows 10/11\n")
                    ef.write("Framework=Python-native Playwright Symmetrical Automation\n")
                    ef.write("Active_URL=https://dummyjson.com / https://www.saucedemo.com\n")
                    
                # Write Executor Metadata to populate the Allure Executors widget beautifully (removing 'Unknown')!
                exec_path = os.path.join(results_path, "executor.json")
                with open(exec_path, "w", encoding="utf-8") as exf:
                    json.dump({
                        "name": "FitNesse Test Automation Runner",
                        "type": "fitnesse",
                        "url": "http://localhost:8080",
                        "buildOrder": 1,
                        "buildName": "Local Run",
                        "buildUrl": "http://localhost:8080/FrontPage"
                    }, exf, indent=2)
                
                # Symmetrical Allure History Copier (Natively preserves Trend and History graphs!)
                prev_history_path = os.path.join(report_path, "history")
                dest_history_path = os.path.join(results_path, "history")
                if os.path.exists(prev_history_path):
                    try:
                        # Copy previous history directory to allure-results before generating
                        shutil.copytree(prev_history_path, dest_history_path, dirs_exist_ok=True)
                    except Exception as hist_err:
                        pass
                
                # Compile the results permanently as a static folder inside your project!
                try:
                    allure_cmd = shutil.which("allure") or os.path.expandvars(r"%APPDATA%\npm\allure.cmd")
                    gen_proc = subprocess.run(f'"{allure_cmd}" generate "{results_path}" -o "{report_path}" --clean', shell=True, capture_output=True, text=True)
                    
                    # Inject a native script inside the compiled HTML to force Allure to load in its premium Dark Mode theme!
                    index_html_path = os.path.join(report_path, "index.html")
                    if os.path.exists(index_html_path):
                        with open(index_html_path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                        if "allure-theme" not in html_content:
                            dark_script = '<script>localStorage.setItem("allure-theme", "dark"); localStorage.setItem("allure-playbook-theme", "dark"); if(!document.body.classList.contains("theme_dark")){document.body.classList.add("theme_dark");}</script>'
                            html_content = html_content.replace("</head>", f"{dark_script}</head>")
                            with open(index_html_path, "w", encoding="utf-8") as f:
                                f.write(html_content)
                        self._send_json(200, {"served": True, "url": "http://localhost:8090/allure/index.html"})
                    else:
                        err_msg = (gen_proc.stderr or gen_proc.stdout or "").strip()
                        self._send_json(400, {"error": f"Allure report generation failed: {err_msg}"})
                except Exception as gen_err:
                    self._send_json(400, {"error": f"Allure CLI error: {str(gen_err)}"})
            except Exception as error:
                self._send_json(500, {"error": str(error)})
            return

        elif self.path.startswith("/files/testResults/"):
            try:
                prefix = "/files/testResults/"
                relative_path = unquote(self.path.split("?", 1)[0][len(prefix):])
                path_parts = relative_path.split("/")
                allowed_folders = {"ui-automation", "visual-regression"}
                if (
                    len(path_parts) != 2
                    or path_parts[0] not in allowed_folders
                    or not path_parts[1]
                    or path_parts[1] != os.path.basename(path_parts[1])
                    or not path_parts[1].lower().endswith(".png")
                ):
                    self._send_json(404, {"error": "Screenshot not found"})
                    return
                screenshot_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "testResults", *path_parts)
                if not os.path.isfile(screenshot_path):
                    self._send_json(404, {"error": "Screenshot not found"})
                    return

                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(os.path.getsize(screenshot_path)))
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.end_headers()
                with open(screenshot_path, "rb") as screenshot_file:
                    self.wfile.write(screenshot_file.read())
            except Exception as error:
                self._send_json(500, {"error": str(error)})
            return

        elif self.path == "/report.html":
            try:
                try:
                    from core.report_generator import generate_html_report
                    generate_html_report()
                except Exception as gen_err:
                    logger.debug(f"Failed to refresh report dynamically: {gen_err}")

                file_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "report.html")
                if os.path.exists(file_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self._send_json(404, {"error": "Report not found"})
            except Exception as error:
                self._send_json(500, {"error": str(error)})
            return

        elif self.path in ("/favicon.ico", "/favicon.png"):
            try:
                ext = "png" if self.path.endswith(".png") else "ico"
                mime = "image/png" if ext == "png" else "image/x-icon"
                fav_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "fitnesse", "images", f"favicon.{ext}")
                if os.path.exists(fav_path):
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with open(fav_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self._send_json(404, {"error": "Favicon not found"})
            except Exception as error:
                self._send_json(500, {"error": str(error)})
            return

        elif self.path == "/logo.png":
            try:
                logo_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "images", "fitnesse-logo.png")
                if os.path.exists(logo_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with open(logo_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self._send_json(404, {"error": "Logo not found"})
            except Exception as error:
                self._send_json(500, {"error": str(error)})
            return

        elif self.path.startswith("/framework-logs"):
            try:
                import glob
                log_dir = os.path.join(BASE_DIR, "logs")
                log_files = sorted(glob.glob(os.path.join(log_dir, "framework-*.log")), reverse=True)
                available_files = [os.path.basename(path) for path in log_files]
                query_string = self.path.split("?", 1)[1] if "?" in self.path else ""
                query = parse_qs(query_string)
                requested_file = query.get("file", [""])[0]
                log_filename = requested_file if requested_file in available_files else (available_files[0] if available_files else "")
                log_path = os.path.join(log_dir, log_filename) if log_filename else ""
                log_content = ""
                if log_path:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as log_file:
                        log_content = log_file.read()

                if query.get("partial", [""])[0] == "1":
                    self._send_json(200, {"filename": log_filename or "N/A", "content": log_content})
                    return

                log_lines = log_content.splitlines()
                if not log_lines:
                    log_lines = ["No log files found in logs/ directory." if not log_filename else "The selected log file is empty."]

                def render_log_line(line_number: int, line: str) -> str:
                    upper_line = line.upper()
                    if "[ERROR]" in upper_line or "[CRITICAL]" in upper_line:
                        severity = "error"
                    elif "[WARNING]" in upper_line or "[WARN]" in upper_line:
                        severity = "warning"
                    elif "[DEBUG]" in upper_line:
                        severity = "debug"
                    else:
                        severity = "info"
                    return f'<div class="log-line level-{severity}" data-level="{severity}"><span class="line-number">{line_number}</span><code>{html.escape(line)}</code></div>'

                log_rows = "".join(render_log_line(number, line) for number, line in enumerate(log_lines, 1))
                file_options = "".join(
                    f'<option value="{html.escape(filename, quote=True)}"{" selected" if filename == log_filename else ""}>{html.escape(filename)}</option>'
                    for filename in available_files
                )

                html_logs = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FitNesse Automation - Framework Execution Logs ({log_filename})</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="shortcut icon" type="image/x-icon" href="/favicon.ico" />
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{ color-scheme: dark; }}
        * {{ box-sizing: border-box; }}
        body {{
            background: #101820;
            color: #e2e8f0;
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 22px 26px;
            display: flex;
            flex-direction: column;
            height: 100dvh;
            min-height: 0;
        }}
        header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            flex-wrap: wrap;
            margin-bottom: 14px;
            border-bottom: 1px solid #33434d;
            padding-bottom: 16px;
        }}
        h1 {{
            font-size: 19px;
            margin: 0;
            font-weight: 800;
            color: #f8fafc;
        }}
        .meta {{
            font-size: 13px;
            color: #a7bac5;
            margin-top: 5px;
        }}
        .actions {{
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 8px;
            flex-wrap: wrap;
        }}
        button, select, input {{ font: inherit; }}
        .control {{
            min-height: 36px;
            background: #1c2a34;
            border: 1px solid #42525c;
            color: #e2e8f0;
            padding: 7px 10px;
            border-radius: 5px;
            font-size: 12px;
        }}
        .control:focus {{
            outline: 2px solid #38bdf8;
            outline-offset: 1px;
        }}
        .log-select {{ min-width: 190px; }}
        .search-input {{ width: min(260px, 48vw); }}
        .btn {{
            min-height: 36px;
            background: #1c2a34;
            border: 1px solid #42525c;
            color: #e2e8f0;
            padding: 7px 11px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: background 0.15s, border-color 0.15s;
        }}
        .btn:hover {{
            background: #263944;
            border-color: #647987;
        }}
        .refresh-toggle {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            min-height: 36px;
            padding: 0 9px;
            border: 1px solid #42525c;
            border-radius: 5px;
            color: #c0ced6;
            font-size: 12px;
            cursor: pointer;
            user-select: none;
        }}
        .refresh-toggle input {{ accent-color: #0891b2; }}
        .log-toolbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 9px;
            color: #a7bac5;
            font-size: 11px;
        }}
        .log-content {{
            flex: 1;
            min-height: 0;
            overflow: auto;
            background: #0b1218;
            border: 1px solid #293943;
            border-radius: 6px;
            scrollbar-color: #50636d #101820;
        }}
        .log-line {{
            display: grid;
            grid-template-columns: 54px minmax(0, 1fr);
            gap: 12px;
            min-height: 27px;
            padding: 4px 12px 4px 0;
            border-bottom: 1px solid rgba(100, 116, 139, 0.11);
            border-left: 3px solid transparent;
        }}
        .log-line:hover {{ background: #14232c; }}
        .log-line[hidden] {{ display: none; }}
        .log-line code {{
            align-self: center;
            font-family: 'Fira Code', monospace;
            font-size: 11px;
            line-height: 1.55;
            color: #d6e1e7;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }}
        .line-number {{
            padding-top: 2px;
            color: #637782;
            font: 10px/1.6 'Fira Code', monospace;
            text-align: right;
            user-select: none;
        }}
        .level-error {{ border-left-color: #fb7185; background: rgba(127, 29, 29, 0.12); }}
        .level-error code {{ color: #fda4af; }}
        .level-warning {{ border-left-color: #fbbf24; }}
        .level-warning code {{ color: #fcd34d; }}
        .level-debug code {{ color: #94a3b8; }}
        .empty-state {{ padding: 28px; color: #94a3b8; text-align: center; font-size: 13px; }}
        @media (max-width: 680px) {{
            body {{ padding: 14px; }}
            header {{ align-items: flex-start; }}
            .actions {{ justify-content: flex-start; width: 100%; }}
            .search-input {{ width: min(210px, 55vw); }}
            .log-select {{ min-width: 150px; }}
            .log-line {{ grid-template-columns: 40px minmax(0, 1fr); gap: 8px; }}
        }}
    </style>
    <script>
        var refreshInterval = null;

        function severityForLine(line) {{
            if (/\\[(ERROR|CRITICAL)\\]/i.test(line)) return "error";
            if (/\\[(WARN|WARNING)\\]/i.test(line)) return "warning";
            if (/\\[DEBUG\\]/i.test(line)) return "debug";
            return "info";
        }}

        function renderLogLines(content, keepScrollAtBottom) {{
            var container = document.getElementById("log-box");
            var wasAtBottom = keepScrollAtBottom || (container.scrollHeight - container.scrollTop - container.clientHeight < 32);
            var lines = (content || "").split(/\\r?\\n/);
            if (lines.length && lines[lines.length - 1] === "") lines.pop();
            container.replaceChildren();

            if (!lines.length) {{
                var empty = document.createElement("div");
                empty.className = "empty-state";
                empty.textContent = "No log entries in this file.";
                container.appendChild(empty);
            }} else {{
                var fragment = document.createDocumentFragment();
                lines.forEach(function(line, index) {{
                    var row = document.createElement("div");
                    row.className = "log-line level-" + severityForLine(line);
                    row.setAttribute("data-level", severityForLine(line));
                    var number = document.createElement("span");
                    number.className = "line-number";
                    number.textContent = String(index + 1);
                    var text = document.createElement("code");
                    text.textContent = line;
                    row.appendChild(number);
                    row.appendChild(text);
                    fragment.appendChild(row);
                }});
                container.appendChild(fragment);
            }}

            applyLogFilters();
            if (wasAtBottom) container.scrollTop = container.scrollHeight;
        }}

        function applyLogFilters() {{
            var query = (document.getElementById("log-search").value || "").toLowerCase();
            var selectedLevel = document.getElementById("log-level").value;
            var rows = document.querySelectorAll(".log-line");
            var visible = 0;
            rows.forEach(function(row) {{
                var matchesText = row.textContent.toLowerCase().indexOf(query) !== -1;
                var matchesLevel = selectedLevel === "all" || row.getAttribute("data-level") === selectedLevel;
                row.hidden = !(matchesText && matchesLevel);
                if (!row.hidden) visible++;
            }});
            document.getElementById("line-count").textContent = visible + " / " + rows.length + " lines";
        }}

        function selectLogFile(filename) {{
            var target = new URL(window.location.href);
            target.searchParams.set("file", filename);
            window.location.assign(target.toString());
        }}

        function downloadLog() {{
            var text = Array.from(document.querySelectorAll(".log-line:not([hidden]) code"))
                .map(function(line) {{ return line.textContent; }}).join("\\n");
            var link = document.createElement("a");
            link.href = URL.createObjectURL(new Blob([text], {{ type: "text/plain;charset=utf-8" }}));
            link.download = document.getElementById("log-file").value || "framework.log";
            link.click();
            URL.revokeObjectURL(link.href);
        }}

        function startAutoRefresh() {{
            clearInterval(refreshInterval);
            refreshInterval = setInterval(function() {{
                refreshLogs(true);
            }}, 3000);
        }}
        
        function toggleAutoRefresh(chk) {{
            if (chk.checked) {{
                startAutoRefresh();
                localStorage.setItem("fitnesse_logs_auto_refresh", "true");
            }} else {{
                clearInterval(refreshInterval);
                localStorage.setItem("fitnesse_logs_auto_refresh", "false");
            }}
        }}

        function refreshLogs(keepScrollAtBottom) {{
            var filename = document.getElementById("log-file").value;
            var status = document.getElementById("log-status");
            fetch("/framework-logs?partial=1&file=" + encodeURIComponent(filename), {{ cache: "no-store" }})
                .then(function(response) {{
                    if (!response.ok) throw new Error("HTTP " + response.status);
                    return response.json();
                }})
                .then(function(data) {{
                    if (data.error) throw new Error(data.error);
                    if (data.filename && data.filename !== "N/A") {{
                        document.getElementById("active-log-name").textContent = data.filename;
                    }}
                    renderLogLines(data.content, keepScrollAtBottom);
                    status.textContent = "Updated " + new Date().toLocaleTimeString();
                }})
                .catch(function(error) {{
                    status.textContent = "Refresh failed: " + error.message;
                }});
        }}
        
        function scrollToBottom() {{
            var container = document.getElementById("log-box");
            if (container) {{
                container.scrollTop = container.scrollHeight;
            }}
        }}
        
        document.addEventListener("DOMContentLoaded", function() {{
            applyLogFilters();
            var autoPref = localStorage.getItem("fitnesse_logs_auto_refresh") !== "false";
            var checkbox = document.getElementById("auto-refresh-toggle");
            checkbox.checked = autoPref;
            if (autoPref) startAutoRefresh();
            scrollToBottom();
        }});
    </script>
</head>
<body>
    <header>
        <div style="display: flex; align-items: center; gap: 14px;">
            <img src="/logo.png" alt="FitNesse Automation" style="height: 48px; width: auto; object-fit: contain;">
            <div>
                <h1>Framework Logs</h1>
                <div class="meta">Daily execution output · <strong id="active-log-name">{html.escape(log_filename or 'N/A')}</strong></div>
            </div>
        </div>
        <div class="actions">
            <select id="log-file" class="control log-select" aria-label="Select log file" onchange="selectLogFile(this.value)">
                {file_options or '<option value="">No log files</option>'}
            </select>
            <input id="log-search" class="control search-input" type="search" placeholder="Search log lines" aria-label="Search log lines" oninput="applyLogFilters()">
            <select id="log-level" class="control" aria-label="Filter severity" onchange="applyLogFilters()">
                <option value="all">All levels</option>
                <option value="error">Errors</option>
                <option value="warning">Warnings</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
            </select>
            <label class="refresh-toggle" title="Refresh the log every 3 seconds">
                <input type="checkbox" id="auto-refresh-toggle" onchange="toggleAutoRefresh(this)" checked>
                <span>Live</span>
            </label>
            <button class="btn" onclick="refreshLogs(false)" title="Refresh now">Refresh</button>
            <button class="btn" onclick="downloadLog()" title="Download visible lines">Download</button>
            <button class="btn" onclick="scrollToBottom()" title="Scroll to latest line">Latest</button>
        </div>
    </header>
    <div class="log-toolbar">
        <span id="line-count">{len(log_lines)} lines</span>
        <span id="log-status">Ready</span>
    </div>
    <main id="log-box" class="log-content" aria-label="Framework log entries">
        {log_rows or '<div class="empty-state">No log entries.</div>'}
    </main>
</body>
</html>"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.end_headers()
                self.wfile.write(html_logs.encode("utf-8"))
            except Exception as error:
                self._send_json(500, {"error": str(error)})
            return

        elif self.path.startswith("/allure"):
            try:
                # Strip query parameters (e.g. "?t=1273918237") to bypass FitNesse blocks and load files cleanly!
                clean_path = self.path.split("?")[0]
                
                # Resolve the physical file path on disk
                relative_file_path = clean_path.replace("/allure", "").lstrip("/")
                if not relative_file_path or relative_file_path == "":
                    relative_file_path = "index.html"
                
                file_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "testResults", "allure-report", relative_file_path)
                
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    # Determine MIME type
                    content_type = "text/plain"
                    if file_path.endswith(".html"):
                        content_type = "text/html"
                    elif file_path.endswith(".js"):
                        content_type = "application/javascript"
                    elif file_path.endswith(".css"):
                        content_type = "text/css"
                    elif file_path.endswith(".json"):
                        content_type = "application/json"
                    elif file_path.endswith(".png"):
                        content_type = "image/png"
                    elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                        content_type = "image/jpeg"
                    elif file_path.endswith(".svg"):
                        content_type = "image/svg+xml"
                    
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    # Force Cache-Busting to prevent browser from caching old Allure report results!
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self._send_json(404, {"error": f"File not found: {relative_file_path}"})
            except Exception as error:
                self._send_json(500, {"error": str(error)})
            return

        elif self.path == "/pop-run":
            try:
                page_name = "UI Test Run"
                if ACTIVE_RUNS_QUEUE:
                    page_name = ACTIVE_RUNS_QUEUE.pop()  # Get and erase so it is one-time use!
                self._send_json(200, {"page_name": page_name})
            except Exception as error:
                self._send_json(400, {"error": str(error)})
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/users":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                users = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(users, dict) or not users:
                    raise ValueError("At least one user is required")
                if not any(user.get("role") == "admin" for user in users.values()):
                    raise ValueError("At least one Admin user must remain")
                write_users(users)
                sync_fitnesse_password_file(users)
                self._send_json(200, {"saved": True})
            except (ValueError, json.JSONDecodeError, OSError) as error:
                self._send_json(400, {"error": str(error)})
            return
            
        elif self.path == "/environments":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict) or not payload:
                    raise ValueError("At least one configuration payload is required")
                update_env_file(payload)
                self._send_json(200, {"saved": True})
            except Exception as error:
                self._send_json(400, {"error": str(error)})
            return
            
        elif self.path == "/live-debug":
            try:
                debug_file = os.path.join(BASE_DIR, "runtime", "live-debug.txt")
                os.makedirs(os.path.dirname(debug_file), exist_ok=True)
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write("true")
                self._send_json(200, {"debug": True})
            except Exception as error:
                self._send_json(400, {"error": str(error)})
            return
            
        elif self.path == "/clear-allure":
            try:
                import glob
                import shutil
                
                # 1. Wipe older Allure results cleanly
                results_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "testResults", "allure-results")
                if os.path.exists(results_path):
                    files = glob.glob(os.path.join(results_path, "*"))
                    for file_path in files:
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        except Exception:
                            pass
                            
                # 2. Wipe older Allure report but preserve 'history' folder for Trend graphs
                report_path = os.path.join(BASE_DIR, "FitNesseRoot", "files", "testResults", "allure-report")
                if os.path.exists(report_path):
                    files = glob.glob(os.path.join(report_path, "*"))
                    for file_path in files:
                        try:
                            if os.path.isdir(file_path) and os.path.basename(file_path).lower() == "history":
                                continue
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        except Exception:
                            pass
                            
                # 3. Wipe Simple Report database and HTML file to prevent historical merging!
                history_json = os.path.join(BASE_DIR, "FitNesseRoot", "files", "report_history.json")
                report_html = os.path.join(BASE_DIR, "FitNesseRoot", "files", "report.html")
                for path in (history_json, report_html):
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception:
                        pass
                        
                # Pre-generate a beautiful, branded "Empty" report so they never see a raw 404!
                try:
                    from core.report_generator import generate_html_report
                    generate_html_report()
                except Exception:
                    pass
                        
                # 4. Clean FitNesse XML test subfolders recursively (excluding allure results/report!)
                test_results_dir = os.path.join(BASE_DIR, "FitNesseRoot", "files", "testResults")
                if os.path.exists(test_results_dir):
                    subdirs = glob.glob(os.path.join(test_results_dir, "*"))
                    for s in subdirs:
                        basename = os.path.basename(s).lower()
                        if basename in ("allure-results", "allure-report", "ui-automation"):
                            continue
                        try:
                            if os.path.isfile(s):
                                os.remove(s)
                            elif os.path.isdir(s):
                                shutil.rmtree(s)
                        except Exception:
                            pass
                            
                self._send_json(200, {"cleared": True})
            except Exception as error:
                self._send_json(400, {"error": str(error)})
            return

        elif self.path == "/register-run":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                page_path = payload.get("page", "")
                if page_path:
                    page_name = page_path.split(".")[-1].split("/")[-1]
                    ACTIVE_RUNS_QUEUE.append(page_name)
                    # Limit queue size to avoid bloat
                    if len(ACTIVE_RUNS_QUEUE) > 10:
                        ACTIVE_RUNS_QUEUE.pop(0)
                self._send_json(200, {"registered": True})
            except Exception as error:
                self._send_json(400, {"error": str(error)})
            return

        self._send_json(404, {"error": "Not found"})

    def log_message(self, format_string, *args):
        return


if __name__ == "__main__":
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        sync_fitnesse_password_file()
        raise SystemExit(0)
    sync_fitnesse_password_file()
    
    # Pre-generate a beautiful, branded "Empty" report on boot so they never see a raw 404!
    try:
        from core.report_generator import generate_html_report
        generate_html_report()
    except Exception:
        pass
        
    ThreadingHTTPServer((HOST, PORT), UserStoreHandler).serve_forever()
