# modulos/qr_generator.py
from flask import Response, render_template_string
import socket
import qrcode
import io
import requests
import base64

def configurar_rutas_qr(app):
    @app.route("/qr")
    def generar_qr():
        ip_local = obtener_ip_local()
        url = f"http://{ip_local}:8080/pose"
        
        qr_base64 = generar_qr_code(url)
        
        html = f"""
        <html>
        <head>
            <title>Acceso Local VR</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: sans-serif;
                    text-align: center;
                    background-color: #111;
                    color: white;
                    margin: 0;
                    padding: 20px;
                }}
                h1 {{ color: #0af; }}
                .url {{ 
                    color: #0f0;
                    word-break: break-all;
                    margin: 20px;
                    padding: 10px;
                    background: #222;
                    border-radius: 5px;
                }}
                img {{ max-width: 80%; height: auto; margin: 20px 0; }}
                .btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    background: #0af;
                    color: #fff;
                    border: none;
                    border-radius: 5px;
                    text-decoration: none;
                    font-weight: bold;
                    margin: 10px;
                }}
            </style>
        </head>
        <body>
            <h1>🎮 Escanea el código QR</h1>
            <div class="url">{url}</div>
            <img src='data:image/png;base64,{qr_base64}'>
            <br>
            <a href="/" class="btn">Volver</a>
        </body>
        </html>
        """
        return render_template_string(html)

    @app.route("/ngrok_qr")
    def generar_qr_ngrok():
        try:
            respuesta = requests.get("http://127.0.0.1:4040/api/tunnels")
            json_data = respuesta.json()
            for tunel in json_data['tunnels']:
                if tunel['proto'] == 'https':
                    url = tunel['public_url'] + "/pose"
                    qr_base64 = generar_qr_code(url)
                    
                    html = f"""
                    <html>
                    <head>
                        <title>Acceso remoto VR</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <style>
                            body {{
                                font-family: sans-serif;
                                text-align: center;
                                background-color: #111;
                                color: white;
                                margin: 0;
                                padding: 20px;
                            }}
                            h1 {{ color: #0af; }}
                            .url {{ 
                                color: #0f0;
                                word-break: break-all;
                                margin: 20px;
                                padding: 10px;
                                background: #222;
                                border-radius: 5px;
                            }}
                            img {{ max-width: 80%; height: auto; margin: 20px 0; }}
                            .btn {{
                                display: inline-block;
                                padding: 10px 20px;
                                background: #0af;
                                color: #fff;
                                border: none;
                                border-radius: 5px;
                                text-decoration: none;
                                font-weight: bold;
                                margin: 10px;
                            }}
                        </style>
                    </head>
                    <body>
                        <h1>🎮 Escanea el código para acceder a tu visor VR</h1>
                        <div class="url">{url}</div>
                        <img src='data:image/png;base64,{qr_base64}'>
                        <br>
                        <a href="/" class="btn">Volver</a>
                    </body>
                    </html>
                    """
                    return render_template_string(html)
            return "No se encontró URL HTTPS de ngrok", 404
        except Exception as e:
            return f"Error al obtener URL de ngrok: {e}", 500

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "localhost"
    finally:
        s.close()
    return ip

def generar_qr_code(url):
    qr = qrcode.make(url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
