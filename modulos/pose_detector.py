# modulos/pose_detector.py
from flask_socketio import emit
from flask import request
import math

# Variables para seguimiento
ultima_posicion_y = {}

def configurar_eventos_pose(socketio):
    @socketio.on('pose')
    def recibir_pose(data):
        ip = request.remote_addr
        print(f"[\U0001f4e1 POSE desde {ip}]")

        try:
            # Puntos clave
            nariz = data[0]
            cadera_izq = data[23]
            cadera_der = data[24]
            hombro_izq = data[11]
            hombro_der = data[12]
            mano_izq = data[15]
            mano_der = data[16]
            codo_izq = data[13]
            codo_der = data[14]
            tobillo_izq = data[27]
            tobillo_der = data[28]
            rodilla_izq = data[25]
            rodilla_der = data[26]

            # Calcular centro de cadera
            cadera = {
                'x': (cadera_izq['x'] + cadera_der['x']) / 2,
                'y': (cadera_izq['y'] + cadera_der['y']) / 2,
                'z': (cadera_izq['z'] + cadera_der['z']) / 2
            }

            # Detectar gestos
            gestos_detectados = detectar_gestos_assassins(
                nariz, cadera, hombro_izq, hombro_der, 
                mano_izq, mano_der, codo_izq, codo_der,
                tobillo_izq, tobillo_der, rodilla_izq, rodilla_der, ip
            )
            
            # Detectar controles para Tron
            controles_tron = detectar_controles_tron(
                nariz, cadera, hombro_izq, hombro_der, 
                mano_izq, mano_der
            )
            
            # Enviar eventos y datos de control
            if gestos_detectados or controles_tron:
                emit('evento_gesto', {
                    'gestos': gestos_detectados,
                    'control': controles_tron,
                    'landmarks': data,
                    'modo': 'assassins_creed'  # o 'tron' según el juego activo
                }, broadcast=True)
                
                # Imprimir para debug
                for evento in gestos_detectados:
                    print(f"🎮 Detectado: {evento}")
                if controles_tron:
                    print(f"🎮 Control: {controles_tron}")
                    
        except Exception as e:
            print("⚠️ Error analizando pose:", e)

def detectar_gestos_assassins(nariz, cadera, hombro_izq, hombro_der, 
                            mano_izq, mano_der, codo_izq, codo_der,
                            tobillo_izq, tobillo_der, rodilla_izq, rodilla_der, ip):
    """Detecta gestos específicos para un juego tipo Assassin's Creed"""
    eventos = []
    
    # Brazos extendidos (posición de planear)
    brazos_extendidos = (
        mano_izq['y'] < hombro_izq['y'] and 
        mano_der['y'] < hombro_der['y'] and
        abs(mano_izq['x'] - hombro_izq['x']) > 0.2 and
        abs(mano_der['x'] - hombro_der['x']) > 0.2
    )

    # Levantar ambos brazos
    brazos_arriba = mano_izq['y'] < hombro_izq['y'] and mano_der['y'] < hombro_der['y']

    # Caminar: alternancia de tobillos
    caminar = abs(tobillo_izq['x'] - tobillo_der['x']) > 0.15

    # Agachado: cadera más baja que la nariz
    agachado = cadera['y'] > nariz['y']

    # Salto - seguimiento por IP
    if ip not in ultima_posicion_y:
        ultima_posicion_y[ip] = cadera['y']
    
    velocidad_y = ultima_posicion_y[ip] - cadera['y']
    ultima_posicion_y[ip] = cadera['y']
    salto = velocidad_y > 0.05  # Umbral de velocidad vertical
    
    # Movimiento sigiloso
    agachado_sigiloso = (
        cadera['y'] > nariz['y'] * 1.3 and  # Muy agachado
        abs(tobillo_izq['x'] - tobillo_der['x']) < 0.1  # Pies juntos
    )
    
    # Golpe/Ataque
    puño_adelante = (
        (mano_izq['z'] < codo_izq['z'] - 0.2) or  # Mano más adelante que codo
        (mano_der['z'] < codo_der['z'] - 0.2)
    )
    
    # Añadir eventos detectados
    if brazos_arriba:
        eventos.append("brazos_arriba")
    if brazos_extendidos:
        eventos.append("planear")
    if salto:
        eventos.append("salto")
    if agachado:
        eventos.append("agachado")
    if agachado_sigiloso:
        eventos.append("sigilo")
    if puño_adelante:
        eventos.append("ataque")
    if caminar:
        eventos.append("caminar")
        
    return eventos

def detectar_controles_tron(nariz, cadera, hombro_izq, hombro_der, mano_izq, mano_der):
    """Detecta controles específicos para un juego tipo Tron"""
    
    # Inclinación para girar
    inclinacion_lateral = (hombro_izq['x'] - hombro_der['x']) / 0.7  # Normalizado (-1 a 1)
    
    # Aceleración 
    agachado_aerodinamico = (
        nariz['y'] > hombro_izq['y'] and 
        nariz['y'] > hombro_der['y'] and
        cadera['y'] < hombro_izq['y'] * 1.2
    )
    
    # Frenado
    posicion_frenado = (
        mano_izq['y'] > cadera['y'] and
        mano_der['y'] > cadera['y'] and
        mano_izq['x'] < cadera['x'] and
        mano_der['x'] > cadera['x']
    )
    
    return {
        "direccion": inclinacion_lateral,  # -1 (izquierda) a 1 (derecha)
        "aceleracion": 1 if agachado_aerodinamico else 0.5,
        "frenado": 1 if posicion_frenado else 0
    }
