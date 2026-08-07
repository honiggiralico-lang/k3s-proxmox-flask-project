from flask import Flask, request
import os
import redis
import pymysql

app = Flask(__name__)

# Configurazione Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Configurazione MySQL
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'password')
MYSQL_DB = os.environ.get('MYSQL_DB', 'guestbook')

def get_redis_connection():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=2)
        r.ping()
        return r
    except redis.exceptions.ConnectionError:
        return None

def get_mysql_connection():
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError:
        return None

def init_db():
    """Crea la tabella nel database se non esiste già."""
    conn = get_mysql_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        conn.close()

# Inizializza il DB all'avvio dell'app
init_db()

@app.route('/', methods=['GET', 'POST'])
def hello():
    # Info Kubernetes
    pod_name = os.environ.get('HOSTNAME', 'Local-Workstation')
    node_name = os.environ.get('NODE_NAME', 'N/A')
    client_ip = request.remote_addr

    # Logica Visite (Redis)
    r = get_redis_connection()
    if r:
        visit_count = r.incr('visit_count')
        redis_status = f"✅ Connesso a Redis su {REDIS_HOST}"
    else:
        visit_count = "N/D"
        redis_status = f"❌ Impossibile connettersi a Redis su {REDIS_HOST}"

    # Logica Messaggi (MySQL)
    mysql_status = f"❌ Impossibile connettersi a MySQL su {MYSQL_HOST}"
    messages = []
    
    conn = get_mysql_connection()
    if conn:
        mysql_status = f"✅ Connesso a MySQL su {MYSQL_HOST}"
        with conn.cursor() as cursor:
            # Se è una POST, salva il messaggio
            if request.method == 'POST':
                msg = request.form.get('message')
                if msg:
                    cursor.execute("INSERT INTO messages (message) VALUES (%s)", (msg,))
                    conn.commit()
            
            # Leggi gli ultimi 10 messaggi
            cursor.execute("SELECT message, created_at FROM messages ORDER BY created_at DESC LIMIT 10")
            messages = cursor.fetchall()
        conn.close()

    # Costruzione HTML
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; border-radius: 10px;">
        <h1>🚀 Multi-Tier Flask Guestbook</h1>
        <p><strong>Stato Cache (Redis):</strong> {redis_status}</p>
        <p><strong>Stato DB (MySQL):</strong> {mysql_status}</p>
        <ul style="font-size: 18px;">
            <li>Pod Name: <b>{pod_name}</b></li>
            <li>Node Name: <b>{node_name}</b></li>
            <li>Client IP: <b>{client_ip}</b></li>
            <li style="color: #d9534f;">Visite Totali: <b>{visit_count}</b></li>
        </ul>
        
        <h2>Lascia un messaggio:</h2>
        <form method="POST">
            <input type="text" name="message" placeholder="Scrivi qualcosa..." required style="padding: 8px; width: 300px;">
            <button type="submit" style="padding: 8px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px;">Invia</button>
        </form>
        
        <h3>Ultimi messaggi (salvati in MySQL):</h3>
        <ul>
    """
    for m in messages:
        html += f"<li><b>{m['created_at']}</b>: {m['message']}</li>"
    
    if not messages:
        html += "<li>Nessun messaggio ancora. Scrivi il primo!</li>"
        
    html += """
        </ul>
    </div>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
