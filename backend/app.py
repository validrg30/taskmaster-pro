import os
import socket
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

def get_db_version():
    try:
        conn = psycopg2.connect(
            host="db",
            database=os.getenv("POSTGRES_DB", "taskdb"),
            user=os.getenv("POSTGRES_USER", "myuser"),
            password=os.getenv("POSTGRES_PASSWORD", "mypassword")
        )
        cur = conn.cursor()
        cur.execute('SELECT version()')
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return f"✅ {version}"
    except Exception as e:
        return f"❌ {str(e)}"

# Endpoint folosit de buton pentru cele 7 request-uri
@app.route('/ping')
def ping():
    return jsonify({
        "hostname": socket.gethostname(),
        "request": "OK"
    })

@app.route('/')
def home():
    hostname = socket.gethostname()
    db_status = get_db_version()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TaskMaster Load Balancer Demo</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #0d1117; color: #c9d1d9; }}
            h1 {{ color: #58a6ff; }}
            .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin: 10px 0; }}
            .hostname {{ color: #3fb950; font-size: 1.2em; font-weight: bold; }}
            .db {{ color: #8b949e; font-size: 0.85em; margin-top: 8px; }}
            button {{
                background: #238636; color: white; border: none;
                padding: 12px 24px; border-radius: 6px; cursor: pointer;
                font-size: 1em; margin: 20px 0;
            }}
            button:hover {{ background: #2ea043; }}
            button:disabled {{ background: #3d4450; cursor: not-allowed; }}
            .result {{ 
                padding: 10px 15px; margin: 5px 0; border-radius: 6px;
                background: #1c2128; border-left: 4px solid #58a6ff;
                animation: fadeIn 0.3s ease;
            }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateX(-10px); }} to {{ opacity: 1; transform: translateX(0); }} }}
            .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; background: #388bfd26; color: #58a6ff; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <h1>🐳 TaskMaster Load Balancer Demo</h1>

        <div class="card">
            <div>Această pagină a fost servită de:</div>
            <div class="hostname">🟢 {hostname}</div>
            <div class="db">{db_status}</div>
        </div>

        <button id="btn" onclick="doRefreshes()">
            🔄 Fă 7 request-uri separate
        </button>

        <div id="results"></div>

        <script>
            async function doRefreshes() {{
                const btn = document.getElementById('btn');
                const results = document.getElementById('results');
                btn.disabled = true;
                btn.textContent = '⏳ Se trimit request-uri...';
                results.innerHTML = '';

                for (let i = 1; i <= 7; i++) {{
                    try {{
                        const response = await fetch('/ping');
                        const data = await response.json();
                        const div = document.createElement('div');
                        div.className = 'result';
                        div.innerHTML = `
                            <span class="badge">Request ${{i}}/7</span>
                            &nbsp; Backend: <strong>${{data.hostname}}</strong>
                        `;
                        results.appendChild(div);
                    }} catch (e) {{
                        const div = document.createElement('div');
                        div.className = 'result';
                        div.style.borderColor = '#f85149';
                        div.textContent = `Request ${{i}}/7: ❌ Eroare`;
                        results.appendChild(div);
                    }}
                    await new Promise(r => setTimeout(r, 300));
                }}

                btn.disabled = false;
                btn.textContent = '🔄 Fă 7 request-uri separate';
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
