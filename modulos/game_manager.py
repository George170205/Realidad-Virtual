# modulos/game_manager.py
import os
import json
from flask import send_from_directory, render_template, request, jsonify

# Directorio para almacenar perfiles de juego
GAMES_DIR = 'data/games'
os.makedirs(GAMES_DIR, exist_ok=True)

# Juegos predefinidos
DEFAULT_GAMES = {
    'assassins_creed': {
        'nombre': "Assassin's Creed VR",
        'descripcion': "Juego de acción y sigilo en primera persona",
        'controles': {
            'brazos_arriba': 'Interactuar con objetos altos',
            'planear': 'Planear desde alturas',
            'salto': 'Saltar obstáculos',
            'agachado': 'Esconderse',
            'sigilo': 'Movimiento sigiloso',
            'ataque': 'Ataque cuerpo a cuerpo',
            'caminar': 'Desplazamiento'
        },
        'umbral_sensibilidad': 0.6,
        'activo': True
    },
    'tron_light_cycle': {
        'nombre': "Tron: Light Cycle",
        'descripcion': "Carreras futuristas de motos de luz",
        'controles': {
            'inclinacion': 'Dirección',
            'agachado': 'Aceleración',
            'brazos_extendidos': 'Frenar',
            'salto': 'Turbo',
            'manos_juntas': 'Activar escudo'
        },
        'umbral_sensibilidad': 0.5,
        'activo': True
    }
}

# Inicializar con juegos predeterminados si no existen
for game_id, game_data in DEFAULT_GAMES.items():
    game_file = os.path.join(GAMES_DIR, f"{game_id}.json")
    if not os.path.exists(game_file):
        with open(game_file, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, ensure_ascii=False, indent=2)

def configurar_rutas_juegos(app, socketio):
    @app.route("/juegos")
    def lista_juegos():
        return render_template("juegos.html")
    
    @app.route("/editor_juegos")
    def editor_juegos():
        return render_template("editor_juegos.html")
    
    @app.route("/editor_juegos/<game_id>")
    def editar_juego(game_id):
        return render_template("editor_juegos.html", game_id=game_id)
    
    @app.route("/api/juegos")
    def api_juegos():
        juegos = []
        for filename in os.listdir(GAMES_DIR):
            if filename.endswith('.json'):
                game_id = filename[:-5]  # quitar extensión .json
                game_file = os.path.join(GAMES_DIR, filename)
                try:
                    with open(game_file, 'r', encoding='utf-8') as f:
                        game_data = json.load(f)
                        game_data['id'] = game_id
                        juegos.append(game_data)
                except Exception as e:
                    print(f"Error leyendo juego {game_id}: {e}")
        
        return jsonify({"juegos": juegos})
    
    @app.route("/api/juegos/<game_id>", methods=["GET"])
    def api_obtener_juego(game_id):
        game_file = os.path.join(GAMES_DIR, f"{game_id}.json")
        
        if not os.path.exists(game_file):
            return jsonify({"error": "Juego no encontrado"}), 404
            
        try:
            with open(game_file, 'r', encoding='utf-8') as f:
                game_data = json.load(f)
                game_data['id'] = game_id
                return jsonify(game_data)
        except Exception as e:
            return jsonify({"error": f"Error leyendo datos: {e}"}), 500
    
    @app.route("/api/juegos/<game_id>", methods=["PUT"])
    def api_actualizar_juego(game_id):
        game_file = os.path.join(GAMES_DIR, f"{game_id}.json")
        
        if not os.path.exists(game_file) and game_id not in DEFAULT_GAMES:
            return jsonify({"error": "Juego no encontrado"}), 404
            
        try:
            game_data = request.json
            
            # Eliminar el campo ID si existe
            if 'id' in game_data:
                del game_data['id']
                
            with open(game_file, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
                
            return jsonify({"mensaje": "Juego actualizado correctamente"})
        except Exception as e:
            return jsonify({"error": f"Error guardando datos: {e}"}), 500
    
    @app.route("/api/juegos", methods=["POST"])
    def api_crear_juego():
        try:
            game_data = request.json
            
            # Validar datos mínimos
            if 'nombre' not in game_data:
                return jsonify({"error": "El juego debe tener un nombre"}), 400
                
            # Generar ID a partir del nombre
            game_id = game_data['nombre'].lower().replace(' ', '_')
            
            # Verificar si ya existe
            game_file = os.path.join(GAMES_DIR, f"{game_id}.json")
            if os.path.exists(game_file):
                return jsonify({"error": "Ya existe un juego con ese nombre"}), 400
                
            # Eliminar el campo ID si existe
            if 'id' in game_data:
                del game_data['id']
                
            # Guardar nuevo juego
            with open(game_file, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
                
            return jsonify({"mensaje": "Juego creado correctamente", "id": game_id})
        except Exception as e:
            return jsonify({"error": f"Error creando juego: {e}"}), 500
    
    @app.route("/api/juegos/<game_id>", methods=["DELETE"])
    def api_eliminar_juego(game_id):
        game_file = os.path.join(GAMES_DIR, f"{game_id}.json")
        
        if not os.path.exists(game_file):
            return jsonify({"error": "Juego no encontrado"}), 404
            
        try:
            os.remove(game_file)
            return jsonify({"mensaje": "Juego eliminado correctamente"})
        except Exception as e:
            return jsonify({"error": f"Error eliminando juego: {e}"}), 500
    
    @app.route("/api/juegos/<game_id>/activar", methods=["POST"])
    def api_activar_juego(game_id):
        game_file = os.path.join(GAMES_DIR, f"{game_id}.json")
        
        if not os.path.exists(game_file):
            return jsonify({"error": "Juego no encontrado"}), 404
            
        try:
            # Desactivar todos los juegos
            for filename in os.listdir(GAMES_DIR):
                if filename.endswith('.json'):
                    other_game_file = os.path.join(GAMES_DIR, filename)
                    with open(other_game_file, 'r', encoding='utf-8') as f:
                        other_game_data = json.load(f)
                    
                    other_game_data['activo'] = False
                    
                    with open(other_game_file, 'w', encoding='utf-8') as f:
                        json.dump(other_game_data, f, ensure_ascii=False, indent=2)
#-----------------------------------------------------------------------------------------------------------            
            # Activar el juego seleccion
            with open(game_file, 'r', encoding='utf-8') as f:
                game_data = json.load(f)
            game_data['activo'] = True
            with open(game_file, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
            return jsonify({"mensaje": "Juego activado correctamente"})
        except Exception as e:
            return jsonify({"error": f"Error activando juego: {e}"}), 500
    
    @app.route("/api/juegos/<game_id>/desactivar", methods=["POST"])
    def api_desactivar_juego(game_id):
        game_file = os.path.join(GAMES_DIR, f"{game_id}.json")
        
        if not os.path.exists(game_file):
            return jsonify({"error": "Juego no encontrado"}), 404
            
        try:
            with open(game_file, 'r', encoding='utf-8') as f:
                game_data = json.load(f)
            
            game_data['activo'] = False
            
            with open(game_file, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
                
            return jsonify({"mensaje": "Juego desactivado correctamente"})
        except Exception as e:
            return jsonify({"error": f"Error desactivando juego: {e}"}), 500
    
    @app.route("/api/juego_activo")
    def api_juego_activo():
        """Obtener el juego actualmente activo"""
        try:
            for filename in os.listdir(GAMES_DIR):
                if filename.endswith('.json'):
                    game_file = os.path.join(GAMES_DIR, filename)
                    with open(game_file, 'r', encoding='utf-8') as f:
                        game_data = json.load(f)
                    
                    if game_data.get('activo', False):
                        game_id = filename[:-5]  # quitar extensión .json
                        game_data['id'] = game_id
                        return jsonify(game_data)
            
            return jsonify({"error": "No hay juegos activos"}), 404
        except Exception as e:
            return jsonify({"error": f"Error obteniendo juego activo: {e}"}), 500
    
    # Configurar eventos del Socket.IO para juegos
    def configurar_eventos_socketio(socketio):
        @socketio.on('solicitar_juego_activo')
        def handle_solicitar_juego():
            for filename in os.listdir(GAMES_DIR):
                if filename.endswith('.json'):
                    game_file = os.path.join(GAMES_DIR, filename)
                    try:
                        with open(game_file, 'r', encoding='utf-8') as f:
                            game_data = json.load(f)
                        
                        if game_data.get('activo', False):
                            game_id = filename[:-5]
                            game_data['id'] = game_id
                            socketio.emit('juego_activo', game_data)
                            return
                    except Exception as e:
                        print(f"Error leyendo juego {filename}: {e}")
            
            # Si no hay juego activo
            socketio.emit('juego_activo', {"error": "No hay juegos activos"})
    
    # Esta función se llama desde el servidor principal para configurar los eventos Socket.IO
    return configurar_eventos_socketio