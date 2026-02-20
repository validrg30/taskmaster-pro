import os
import socket
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host="db",
        database=os.getenv("POSTGRES_DB", "taskdb"),
        user=os.getenv("POSTGRES_USER", "myuser"),
        password=os.getenv("POSTGRES_PASSWORD", "mypassword")
    )

def log_and_get_requests(client_ip, container_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Ne asigurăm că există tabelul în baza de date
        cur.execute('''
            CREATE TABLE IF NOT EXISTS request_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip VARCHAR(50),
                container VARCHAR(50)
            )
        ''')
        
        # 2. Salvăm vizita curentă
        cur.execute('INSERT INTO request_logs (ip, container) VALUES (%s, %s)', (client_ip, container_id))
        conn.commit()
        
        # 3. Extragem ultimele 10 vizite pentru a le afișa
        cur.execute("SELECT TO_CHAR(timestamp, 'HH24:MI:SS'), ip, container FROM request_logs ORDER BY id DESC LIMIT 10")
        logs = cur.fetchall()
        
        cur.close()
        conn.close()
        return logs
    except Exception as e:
        return str(e)

# Endpoint-ul ascuns (folosit de butonul de refresh)
@app.route('/ping')
def ping():
    hostname = socket.gethostname()
    client_ip = request.remote_addr
    
    # Salvăm în DB și request-urile făcute de buton!
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO request_logs (ip, container) VALUES (%s, %s)', (client_ip, hostname))
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass

    return jsonify({
        "hostname": hostname,
        "request": "OK"
    })

@app.route('/')
def home():
    hostname = socket.gethostname()
    client_ip = request.remote_addr
    
    # Salvăm accesarea paginii și luăm istoricul
    logs = log_and_get_requests(client_ip, hostname)
    
    # Generăm codul HTML pentru istoricul DB
    logs_html = ""
    if isinstance(logs, str):
        logs_html = f"<div style='color:#f85149;'>Eroare DB: {logs}</div>"
    else:
        for row in logs:
            logs_html += f"<li>🕒 {row[0]} | 💻 IP: {row[1]} | 🟢 Răspuns dat de: <b>{row[2]}</b></li>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TaskMaster Load Balancer</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #0d1117; color: #c9d1d9; }}
            h1, h2 {{ color: #58a6ff; }}
            .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin: 10px 0; }}
            .hostname {{ color: #3fb950; font-size: 1.2em; font-weight: bold; }}
            button {{ background: #238636; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 1em; margin: 10px 0; }}
            button:hover {{ background: #2ea043; }}
            button:disabled {{ background: #3d4450; cursor: not-allowed; }}
            .result {{ padding: 10px; margin: 5px 0; background: #1c2128; border-left: 4px solid #58a6ff; border-radius: 4px; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ background: #161b22; margin: 5px 0; padding: 10px; border-radius: 4px; border: 1px solid #30363d; font-family: monospace; }}
        </style>
    </head>
    <body>
        <h1>🐳 TaskMaster Multi-Container</h1>

        <div class="card">
            <div>Această pagină principală a fost încărcată de:</div>
            <div class="hostname">🟢 {hostname}</div>
        </div>

        <button id="btn" onclick="doRefreshes()">🔄 Generează 7 request-uri rapide</button>
        <div id="results"></div>

        <h2>📜 Ultimele 10 accesări (salvate în PostgreSQL)</h2>
        <p><i>*Apasă F5 pe pagină după ce folosești butonul de sus, pentru a vedea cum cele 7 cereri s-au salvat în baza de date!</i></p>
        <ul>
            {logs_html}
        </ul>

        <script>
            async function doRefreshes() {{
                const btn = document.getElementById('btn');
                const results = document.getElementById('results');
                btn.disabled = true;
                btn.textContent = '⏳ Se procesează...';
                results.innerHTML = '';

                for (let i = 1; i <= 7; i++) {{
                    try {{
                        const response = await fetch('/ping');
                        const data = await response.json();
                        results.innerHTML += `<div class="result">Request ${{i}}/7 → Procesat de <b>${{data.hostname}}</b></div>`;
                    }} catch (e) {{
                        results.innerHTML += `<div class="result" style="border-left-color:#f85149;">Request ${{i}}/7 → Eroare</div>`;
                    }}
                    await new Promise(r => setTimeout(r, 200)); // Mică pauză
                }}

                btn.disabled = false;
                btn.textContent = '🔄 Generează 7 request-uri rapide';
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
