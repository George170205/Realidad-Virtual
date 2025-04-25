from flask import Response, request, jsonify, send_from_directory
import cv2
import ipaddress

# Diccionario para almacenar streams de cámaras
camaras_conectadas = {}

def configurar_rutas_camara(app, socketio):
    @app.route("/video_feed/<ip>")
    def video_feed(ip):
        if ip in camaras_conectadas:
            return Response(generar_frames(ip), mimetype='multipart/x-mixed-replace; boundary=frame')
        else:
            return "Cámara no conectada", 404

    @app.route("/conectar_camara", methods=["POST"])
    def conectar_camara():
        data = request.json
        ip = data.get("ip")

        # Validar formato IP
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return jsonify({"error": "IP no válida"}), 400

        if ip in camaras_conectadas:
            return jsonify({"mensaje": "La cámara ya está conectada"})

        url = f"http://{ip}:8080/video"
        cap = cv2.VideoCapture(url)

        if cap.isOpened():
            camaras_conectadas[ip] = cap
            socketio.emit("nueva_camara", {"ip": ip})  # Avisar al cliente
            return jsonify({"mensaje": "Cámara conectada correctamente"})
        else:
            return jsonify({"error": "No se pudo conectar a la cámara"}), 400

    @app.route("/desconectar_camara/<ip>", methods=["DELETE","POST"])
    def desconectar_camara(ip):
        cap = camaras_conectadas.get(ip)
        if cap:
            cap.release()
            del camaras_conectadas[ip]
            socketio.emit("camara_desconectada", {"ip": ip})
            return jsonify({"mensaje": "Cámara desconectada"})
        return jsonify({"error": "Cámara no encontrada"}), 404

    @app.route("/ver_camaras")
    def ver_camaras():
        return send_from_directory("templates", "ver_camaras.html")
    
    @app.route("/api/camaras")
    def api_camaras():
        return jsonify({"camaras": obtener_lista_camaras()})

def generar_frames(ip):
    cap = camaras_conectadas[ip]
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        cap.release()
        if ip in camaras_conectadas:
            del camaras_conectadas[ip]

def obtener_lista_camaras():
    return list(camaras_conectadas.keys())
