# app.py - Archivo principal del servidor
import eventlet
eventlet.monkey_patch()

from flask import Flask, send_from_directory,Response
from flask_socketio import SocketIO
import os

# Módulos del sistema
from modulos.camara_manager import configurar_rutas_camara
from modulos.pose_detector import configurar_eventos_pose
from modulos.qr_generator import configurar_rutas_qr
from modulos.calibracion_manager import configurar_calibracion
from modulos.video_feed import gen_frames

# Asegurar que los directorios necesarios existen
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Inicializar aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'holograficosys2025!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurar rutas principales
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/pose")
def pose_page():
    return send_from_directory("static", "pose_cliente.html")

@app.route("/calibracion")
def calibracion():
    return send_from_directory("templates", "calibracion.html")

@app.route("/diagnostico")
def diagnostico():
    return send_from_directory("static", "pose_diagnostico.html")

@app.route("/test")
def test():
    print("✅ El celular ha hecho contacto con el servidor.")
    return "¡Servidor conectado correctamente desde el celular!"



# Configurar todos los módulos
configurar_rutas_camara(app, socketio)
configurar_eventos_pose(socketio)
configurar_rutas_qr(app)
configurar_calibracion(app, socketio)  # 👈 ¡Agregado aquí!

# Iniciar servidor
if __name__ == "__main__":
    print("🚀 Servidor iniciado en http://localhost:8080")
    socketio.run(app, host="0.0.0.0", port=8080)