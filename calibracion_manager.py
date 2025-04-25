# modulos/calibracion_manager.py
from flask import request, jsonify, Response
from flask_socketio import SocketIO, emit
import threading
import time
import cv2
import json
import numpy as np
import os

# Variables globales
calibration_running = False
socketio_ref = None  # Referencia global a SocketIO para usar dentro de hilos
active_camera = 0
stream_active = False
pose_data = {}  # Para almacenar los datos de pose más recientes

# Función para configurar las rutas y eventos
def configurar_calibracion(app, socketio):
    global socketio_ref
    socketio_ref = socketio

    # Asegurar que existe el directorio config
    os.makedirs('config', exist_ok=True)

    # Ruta para obtener cámaras disponibles
    @app.route('/api/camaras')
    def obtener_camaras():
        disponibles = []
        for i in range(5):  # Probamos hasta 5 cámaras
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    disponibles.append({"id": str(i), "name": f"Cámara {i}"})
                cap.release()
        return jsonify(disponibles)

    # Ruta para guardar configuración de calibración
    @app.route('/api/guardar_calibracion', methods=['POST'])
    def guardar_calibracion():
        data = request.get_json()
        print("✅ Configuración de calibración guardada:", data)
        # Aquí puedes guardar en un archivo de configuración si lo necesitas
        with open('config/calibracion.json', 'w') as f:
            json.dump(data, f)
        return jsonify({"status": "ok"})

    # Ruta para iniciar stream de video
    @app.route('/api/iniciar_stream')
    def iniciar_stream():
        global active_camera, stream_active
        camera_id = request.args.get('camara', '0')
        active_camera = int(camera_id)
        stream_active = True
        print(f"✅ Iniciando stream de cámara {active_camera}")
        return jsonify({"status": "ok"})

    # Ruta para el feed de video
    @app.route('/calibracion_video_feed')
    def calibracion_video_feed():
        global active_camera
        camera_param = request.args.get('camera', '0')
        if camera_param.isdigit():
            active_camera = int(camera_param)
        return Response(generar_frames(), 
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    # Socket.IO: Iniciar calibración
    @socketio.on('start_calibration')
    def start_calibration(data):
        global calibration_running
        calibration_running = True

        camera_id = int(data.get("cameraId", 0))
        sensibilidad = data.get("sensitivity", 50) / 100.0  # Convertir a escala 0-1
        threshold = data.get("threshold", 30) / 100.0       # Convertir a escala 0-1

        print(f"⚙️ Iniciando calibración: Cámara={camera_id}, Sensibilidad={sensibilidad}, Umbral={threshold}")
        
        # Iniciar hilo de calibración
        hilo = threading.Thread(target=proceso_calibracion, 
                               args=(camera_id, sensibilidad, threshold))
        hilo.daemon = True
        hilo.start()

    # Socket.IO: Detener calibración
    @socketio.on('stop_calibration')
    def stop_calibration():
        global calibration_running, stream_active
        calibration_running = False
        stream_active = False
        print("🛑 Calibración detenida")

    # Socket.IO: Actualizar sensibilidad
    @socketio.on('update_sensitivity')
    def update_sensitivity(data):
        value = data.get('value', 50) / 100.0
        print(f"⚙️ Sensibilidad actualizada: {value}")
        # Aquí puedes actualizar la configuración en tiempo real si es necesario

    # Socket.IO: Actualizar umbral
    @socketio.on('update_threshold')
    def update_threshold(data):
        value = data.get('value', 30) / 100.0
        print(f"⚙️ Umbral actualizado: {value}")
        # Aquí puedes actualizar la configuración en tiempo real si es necesario

# Función para generar frames para el stream de video
def generar_frames():
    global active_camera, stream_active, pose_data
    
    # Inicializar la cámara
    cap = cv2.VideoCapture(active_camera)
    if not cap.isOpened():
        print(f"❌ Error: No se pudo abrir la cámara {active_camera}")
        return
    
    # Configurar resolución (ajustar según sea necesario)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    stream_active = True
    print(f"✅ Stream iniciado en cámara {active_camera}")
    
    try:
        while stream_active:
            success, frame = cap.read()
            if not success:
                print("❌ Error al leer frame")
                break
                
            # Procesar frame para detección de pose (simulado aquí)
            processed_frame, keypoints = procesar_frame_pose(frame)
            
            # Enviar datos de pose vía Socket.IO
            if socketio_ref and keypoints:
                socketio_ref.emit('pose_data', {'keypoints': keypoints})
            
            # Codificar frame para streaming
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if not ret:
                continue
                
            # Construir respuesta para multipart
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
    except Exception as e:
        print(f"❌ Error en stream de video: {e}")
    finally:
        stream_active = False
        cap.release()
        print("🛑 Stream finalizado")

# Función para procesar frame y detectar pose (simulada)
def procesar_frame_pose(frame):
    # Esta función simula la detección de pose
    # En un sistema real, usarías MediaPipe, OpenPose u otra biblioteca
    
    height, width = frame.shape[:2]
    
    # Simular puntos de esqueleto (para pruebas)
    # En producción, reemplaza esto con tu detector de pose real
    keypoints = []
    
    # Nariz (centro superior)
    keypoints.append({"x": 0.5, "y": 0.2, "score": 0.9})
    
    # Ojos
    keypoints.append({"x": 0.45, "y": 0.2, "score": 0.8})  # Ojo izquierdo
    keypoints.append({"x": 0.55, "y": 0.2, "score": 0.8})  # Ojo derecho
    
    # Orejas
    keypoints.append({"x": 0.4, "y": 0.22, "score": 0.7})  # Oreja izquierda
    keypoints.append({"x": 0.6, "y": 0.22, "score": 0.7})  # Oreja derecha
    
    # Hombros
    keypoints.append({"x": 0.4, "y": 0.3, "score": 0.9})   # Hombro izquierdo
    keypoints.append({"x": 0.6, "y": 0.3, "score": 0.9})   # Hombro derecho
    
    # Codos
    keypoints.append({"x": 0.3, "y": 0.4, "score": 0.8})   # Codo izquierdo
    keypoints.append({"x": 0.7, "y": 0.4, "score": 0.8})   # Codo derecho
    
    # Muñecas
    keypoints.append({"x": 0.25, "y": 0.5, "score": 0.7})  # Muñeca izquierda
    keypoints.append({"x": 0.75, "y": 0.5, "score": 0.7})  # Muñeca derecha
    
    # Caderas
    keypoints.append({"x": 0.45, "y": 0.6, "score": 0.9})  # Cadera izquierda
    keypoints.append({"x": 0.55, "y": 0.6, "score": 0.9})  # Cadera derecha
    
    # Rodillas
    keypoints.append({"x": 0.45, "y": 0.75, "score": 0.8}) # Rodilla izquierda
    keypoints.append({"x": 0.55, "y": 0.75, "score": 0.8}) # Rodilla derecha
    
    # Tobillos
    keypoints.append({"x": 0.45, "y": 0.9, "score": 0.7})  # Tobillo izquierdo
    keypoints.append({"x": 0.55, "y": 0.9, "score": 0.7})  # Tobillo derecho
    
    # Dibujar los puntos en el frame para visualización
    for point in keypoints:
        x, y = int(point["x"] * width), int(point["y"] * height)
        cv2.circle(frame, (x, y), 5, (0, 170, 255), -1)
    
    # Dibujar conexiones entre puntos
    connections = [
        (5, 6),    # Hombros
        (5, 7),    # Hombro izq a codo izq
        (7, 9),    # Codo izq a muñeca izq
        (6, 8),    # Hombro der a codo der
        (8, 10),   # Codo der a muñeca der
        (5, 11),   # Hombro izq a cadera izq
        (6, 12),   # Hombro der a cadera der
        (11, 12),  # Caderas
        (11, 13),  # Cadera izq a rodilla izq
        (13, 15),  # Rodilla izq a tobillo izq
        (12, 14),  # Cadera der a rodilla der
        (14, 16)   # Rodilla der a tobillo der
    ]
    
    for connection in connections:
        if len(keypoints) > max(connection):
            pt1 = (int(keypoints[connection[0]]["x"] * width), 
                   int(keypoints[connection[0]]["y"] * height))
            pt2 = (int(keypoints[connection[1]]["x"] * width), 
                   int(keypoints[connection[1]]["y"] * height))
            cv2.line(frame, pt1, pt2, (0, 170, 255), 2)
    
    return frame, keypoints

# Proceso de calibración (simulado)
def proceso_calibracion(camera_id, sensibilidad, threshold):
    global calibration_running, socketio_ref
    
    if not socketio_ref:
        print("❌ Error: Socket.IO no inicializado")
        return
    
    print(f"⚙️ Iniciando proceso de calibración")
    time.sleep(2)  # Pequeña pausa para inicialización
    
    # Simular los pasos de calibración
    pasos = ["arms", "squat", "jump"]
    progress = 0
    
    for paso in pasos:
        if not calibration_running:
            print("🛑 Calibración interrumpida")
            return
        
        # Simular tiempo de espera para cada paso
        for _ in range(3):
            if not calibration_running:
                return
            time.sleep(1)
            progress += 10
            socketio_ref.emit('calibration_progress', {"progress": progress})
        
        # Marcar paso como completado
        print(f"✅ Paso de calibración completado: {paso}")
        socketio_ref.emit('calibration_update', {paso: True})
    
    if calibration_running:
        print("✅ Calibración completa")
        socketio_ref.emit('calibration_done')
    
    calibration_running = False