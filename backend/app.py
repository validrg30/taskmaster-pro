import os
from flask import Flask
from datetime import datetime
import psycopg2

app = Flask(__name__)

DB_CONFIG = {
    "host": "db",
    "database": "taskdb",
    "user": "myuser",
    "password": "mypassword"
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    """Creează tabela dacă nu există (rulat la startup)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id        SERIAL PRIMARY KEY,
            hostname  TEXT NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def home():
    hostname = os.getenv('HOSTNAME', 'unknown')
    try:
        conn = get_conn()
        cur = conn.cursor()

        # 1️⃣ Inserăm log-ul curent
        cur.execute(
            "INSERT INTO request_logs (hostname) VALUES (%s)",
            (hostname,)
        )
        conn.commit()

        # 2️⃣ Citim ultimele 10 loguri
        cur.execute("""
            SELECT id, hostname, timestamp
            FROM request_logs
            ORDER BY id DESC
            LIMIT 10
        """)
        logs = cur.fetchall()

        cur.close()
        conn.close()

        # 3️⃣ Construim HTML-ul
        rows = "".join(
            f"<tr><td>#{row[0]}</td><td>{row[1]}</td><td>{row[2].strftime('%Y-%m-%d %H:%M:%S')}</td></tr>"
            for row in logs
        )

        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: monospace; padding: 20px; background: #1e1e2e; color: #cdd6f4; }}
                h2 {{ color: #89b4fa; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #45475a; padding: 8px 12px; text-align: left; }}
                th {{ background: #313244; color: #cba6f7; }}
                tr:nth-child(even) {{ background: #181825; }}
                tr:first-child {{ background: #a6e3a1; color: #1e1e2e; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h2>🟢 Backend: <code>{hostname}</code></h2>
            <h3>📋 Ultimele 10 request-uri:</h3>
            <table>
                <tr><th>#</th><th>Hostname (container)</th><th>Timestamp</th></tr>
                {rows}
            </table>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h2>🔴 Backend: <code>{hostname}</code> | Eroare: {e}</h2>"


if __name__ == "__main__":
    init_db()  # 👈 Inițializare la pornire
    app.run(host='0.0.0.0', port=5000)
