from flask import Flask, request
import os
import redis

app = Flask(__name__)

# Configurazione Redis: cerca la variabile d'ambiente REDIS_HOST (per K8s), 
# altrimenti usa 'localhost' (per il test locale sulla tua workstation)
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

def get_redis_connection():
    try:
        # decode_responses=True fa sì che Redis restituisca stringhe invece di byte
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=2)
        r.ping() # Verifica che la connessione funzioni
        return r
    except redis.exceptions.ConnectionError:
        return None

@app.route('/')
def hello():
    # Info di Kubernetes (saranno valorizzate quando deployeremo)
    pod_name = os.environ.get('HOSTNAME', 'Local-Workstation')
    node_name = os.environ.get('NODE_NAME', 'N/A')
    client_ip = request.remote_addr

    r = get_redis_connection()
    
    if r:
        # Incrementa il contatore delle visite
        visit_count = r.incr('visit_count')
        db_status = f"✅ Connesso a Redis su {REDIS_HOST}"
    else:
        visit_count = "N/D (DB Offline)"
        db_status = f"❌ Impossibile connettersi a Redis su {REDIS_HOST}:{REDIS_PORT}"

    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; border-radius: 10px;">
        <h1>🚀 Multi-Tier Flask App - Auto-Deployed  via CI/CD!</h1>
        <p><strong>Stato DB:</strong> {db_status}</p>
        <ul style="font-size: 18px;">
            <li>Pod Name: <b>{pod_name}</b></li>
            <li>Node Name: <b>{node_name}</b></li>
            <li>Client IP: <b>{client_ip}</b></li>
            <li style="color: #d9534f;">Visite Totali: <b>{visit_count}</b></li>
        </ul>
        <p>Aggiorna la pagina per aumentare il contatore!</p>
    </div>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
