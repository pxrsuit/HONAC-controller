from flask import Flask, request, jsonify, render_template
import pydirectinput
import threading
import time
import winsound
import socket
import logging
from waitress import serve

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

pydirectinput.PAUSE = 0.05
app = Flask(__name__)

state = {
    'siren': False, 'blue': False, 
    'flood_l': False, 'flood_r': False, 'horn': False,
    'stop_up': False, 'stop_down': False, 'volg': False,
    'green': False, 'amber': False,
    'kk': False, 'power': False
}

keys = {
    'green': '4', 'amber': '2',
    'kk': '', 'power': '' # EMPTY CONFIG FOR NLPDFR
}

stop_beeping = True

def beep_loop():
    global stop_beeping
    while not stop_beeping:
        try:
            winsound.Beep(1500, 150)
            time.sleep(0.1)
            winsound.Beep(1500, 150)
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"Fout bij afspelen pieptoon: {e}")
            break

def turn_off_others(exclude=[]):
    global state, stop_beeping
    
    if 'blue' not in exclude and state['blue']:
        pydirectinput.press('1')
        state['blue'] = False
        
    if 'siren' not in exclude and state['siren']:
        pydirectinput.keyDown('alt')
        time.sleep(1.0)
        pydirectinput.keyUp('alt')
        state['siren'] = False

    if 'flood_l' not in exclude and (state['flood_l'] or state['flood_r'] or state['horn']):
        pydirectinput.press('5')
        state['flood_l'] = state['flood_r'] = state['horn'] = False

    if 'stop_down' not in exclude and (state['stop_up'] or state['stop_down'] or state['volg']):
        pydirectinput.press('3')
        state['stop_up'] = state['stop_down'] = state['volg'] = False
        stop_beeping = True

    for k in ['green', 'amber', 'kk', 'power']:
        if k not in exclude and state[k]:
            if keys.get(k):
                pydirectinput.press(keys[k])
            state[k] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/toggle', methods=['POST'])
def toggle():
    global stop_beeping
    data = request.json
    btn = data.get('button')
    
    if btn not in state:
        return jsonify({"error": "Ongeldige knop"}), 400
    
    try:
        # --- 1. SIRENE ---
        if btn == 'siren':
            if not state['siren']:
                pydirectinput.press('alt')
                state['siren'] = True
                
                if not state['blue']:
                    pydirectinput.press('1')
                    state['blue'] = True
                    
                turn_off_others(exclude=['siren', 'blue'])
                logger.info("[ROOD] Sirene + Blauw AAN")
            else:
                pydirectinput.keyDown('alt')
                time.sleep(1.0)
                pydirectinput.keyUp('alt')
                state['siren'] = False
                logger.info("[ROOD] Alleen Sirene UIT")

        # --- 2. BLAUW ---
        elif btn == 'blue':
            state['blue'] = not state['blue']
            pydirectinput.press('1')
            
            if state['blue']:
                turn_off_others(exclude=['siren', 'blue'])
                logger.info("[BLAUW] AAN")
            else:
                logger.info("[BLAUW] UIT")

        # --- 3. FLOOD LGHTS ---
        elif btn in ['flood_l', 'flood_r', 'horn']:
            new_state = not state['flood_l']
            pydirectinput.press('5')
            
            state['flood_l'] = new_state
            state['flood_r'] = new_state
            state['horn'] = new_state
            
            if new_state:
                turn_off_others(exclude=['flood_l', 'flood_r', 'horn'])
                logger.info("[FLOOD LIGHTS] AAN")
            else:
                logger.info("[FLOOD LIGHTS] UIT")

        # --- 4. STOP/VOLG ---
        elif btn in ['stop_up', 'stop_down', 'volg']:
            new_state = not state['stop_up']
            pydirectinput.press('3')
            
            state['stop_up'] = new_state
            state['stop_down'] = new_state
            state['volg'] = new_state
            
            if new_state:
                turn_off_others(exclude=['stop_up', 'stop_down', 'volg'])
                stop_beeping = False
                threading.Thread(target=beep_loop, daemon=True).start()
                logger.info("[STOP/VOLG] AAN + PIEPEN")
            else:
                stop_beeping = True
                logger.info("[STOP/VOLG] UIT")

        # --- 5. OVERIG ---
        else:
            state[btn] = not state[btn]
            
            if keys.get(btn):
                pydirectinput.press(keys[btn])
            
            if state[btn]:
                turn_off_others(exclude=[btn])
                logger.info(f"[{btn.upper()}] AAN")
            else:
                logger.info(f"[{btn.upper()}] UIT")
                
    except Exception as e:
        logger.error(f"Fout bij het uitvoeren van actie {btn}: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify(state)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    ip = get_ip()
    logger.info("="*50)
    logger.info(" HONAC CONTROLLER ACTIEF")
    logger.info(f" Open op je apparaat: http://{ip}:5000")
    logger.info("="*50)
    serve(app, host='0.0.0.0', port=5000)
