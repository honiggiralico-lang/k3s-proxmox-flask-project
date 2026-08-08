from flask import Flask, request
import os
import redis
import pymysql
import json
import urllib.request
import ssl

app = Flask(__name__)

# Redis Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# MySQL Configuration
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
    """Creates the database table if it doesn't already exist."""
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

def get_node_os(node_name):
    """Query K8s API to get the OS of the node where the pod is running."""
    if node_name == "N/A" or node_name == "Local-Workstation":
        return "Local OS"
    try:
        # K8s internal API URL
        api_url = f"https://kubernetes.default.svc/api/v1/nodes/{node_name}"
        token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        ca_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        
        with open(token_path, 'r') as f:
            token = f.read()
            
        req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}"})
        context = ssl.create_default_context()
        context.load_verify_location(ca_path)
        
        with urllib.request.urlopen(req, context=context) as response:
            node_data = json.loads(response.read().decode('utf-8'))
            return node_data['status']['nodeInfo']['osImage']
    except Exception as e:
        return f"Error fetching OS: {str(e)}"

# Initialize DB on app startup
init_db()

@app.route('/', methods=['GET', 'POST'])
def hello():
    # Kubernetes Info
    pod_name = os.environ.get('HOSTNAME', 'Local-Workstation')
    # NODE_NAME is passed via Downward API in the YAML
    node_name = os.environ.get('NODE_NAME', 'N/A')
    node_os = get_node_os(node_name)
    client_ip = request.remote_addr

    # Visit Counter Logic (Redis)
    r = get_redis_connection()
    if r:
        visit_count = r.incr('visit_count')
        redis_status = f"✅ Connected to Redis on {REDIS_HOST}"
    else:
        visit_count = "N/A"
        redis_status = f"❌ Cannot connect to Redis on {REDIS_HOST}"

    # Messages Logic (MySQL)
    mysql_status = f"❌ Cannot connect to MySQL on {MYSQL_HOST}"
    messages = []
    
    conn = get_mysql_connection()
    if conn:
        mysql_status = f"✅ Connected to MySQL on {MYSQL_HOST}"
        with conn.cursor() as cursor:
            if request.method == 'POST':
                msg = request.form.get('message')
                if msg:
                    cursor.execute("INSERT INTO messages (message) VALUES (%s)", (msg,))
                    conn.commit()
            
            cursor.execute("SELECT message, created_at FROM messages ORDER BY created_at DESC LIMIT 10")
            messages = cursor.fetchall()
        conn.close()

    # HTML Construction
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; border-radius: 10px;">
        <h1>🚀 Multi-Tier Flask Guestbook</h1>
        <p><strong>Cache Status (Redis):</strong> {redis_status}</p>
        <p><strong>DB Status (MySQL):</strong> {mysql_status}</p>
        <ul style="font-size: 18px;">
            <li>Pod Name: <b>{pod_name}</b></li>
            <li>Node Name: <b>{node_name}</b></li>
            <li>Node OS: <b>{node_os}</b></li>
            <li>Client IP: <b>{client_ip}</b></li>
            <li style="color: #d9534f;">Total Visits: <b>{visit_count}</b></li>
        </ul>
        
        <h2>Leave a message:</h2>
        <form method="POST">
            <input type="text" name="message" placeholder="Write something..." required style="padding: 8px; width: 300px;">
            <button type="submit" style="padding: 8px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px;">Submit</button>
        </form>
        
        <h3>Latest messages (saved in MySQL):</h3>
        <ul>
    """
    for m in messages:
        html += f"<li><b>{m['created_at']}</b>: {m['message']}</li>"
    
    if not messages:
        html += "<li>No messages yet. Write the first one!</li>"
        
    html += """
        </ul>
    </div>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
