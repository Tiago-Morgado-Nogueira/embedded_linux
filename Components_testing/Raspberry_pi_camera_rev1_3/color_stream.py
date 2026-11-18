import cv2
import numpy as np
import webcolors
from collections import deque
from flask import Flask, Response, jsonify
from picamera2 import Picamera2

app = Flask(__name__)

# Variável global para armazenar a última cor detetada (para o painel lateral)
current_detected_color = {"name": "A procurar...", "rgb": (100, 100, 100)}

# Inicializar e configurar a câmara OV5647
picam2 = Picamera2()
camera_config = picam2.create_video_configuration(main={"size": (1280, 720)})
picam2.configure(camera_config)
picam2.start()

def get_closest_color_name(rgb_tuple):
    r, g, b = rgb_tuple
    
    if r < 40 and g < 40 and b < 40:
        return "Black", (0, 0, 0)
    if r > 220 and g > 220 and b > 220:
        return "White", (255, 255, 255)
    if abs(r - g) < 15 and abs(g - b) < 15 and 40 <= r <= 220:
        return "Gray", (128, 128, 128)

    min_distance = float('inf')
    closest_name = "Unknown"
    
    for hex_val, name in webcolors.CSS3_HEX_TO_NAMES.items():
        cr, cg, cb = webcolors.hex_to_rgb(hex_val)
        distance = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if distance < min_distance:
            min_distance = distance
            closest_name = name

    return closest_name.replace("_", " ").title(), (int(r), int(g), int(b))

def generate_frames():
    global current_detected_color
    rgb_history = deque(maxlen=10)
    
    while True:
        frame = picam2.capture_array()
        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        hsv = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([0, 40, 40])
        upper_bound = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area > 1200:
                x, y, w, h = cv2.boundingRect(largest_contour)
                roi_bgr = bgr_frame[y:y+h, x:x+w]
                
                mean_b = np.mean(roi_bgr[:, :, 0])
                mean_g = np.mean(roi_bgr[:, :, 1])
                mean_r = np.mean(roi_bgr[:, :, 2])
                
                rgb_history.append((mean_r, mean_g, mean_b))
                
                avg_r = np.mean([item[0] for item in rgb_history])
                avg_g = np.mean([item[1] for item in rgb_history])
                avg_b = np.mean([item[2] for item in rgb_history])
                
                color_name, rgb_color = get_closest_color_name((avg_r, avg_g, avg_b))
                box_color = (int(rgb_color[2]), int(rgb_color[1]), int(rgb_color[0]))
                
                # Atualizar variável global para o painel lateral
                current_detected_color["name"] = color_name
                current_detected_color["rgb"] = rgb_color
                
                cv2.rectangle(bgr_frame, (x, y), (x + w, y + h), box_color, 3)
                cv2.putText(bgr_frame, f"Cor: {color_name}", (x, y - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
            else:
                if len(rgb_history) > 0:
                    rgb_history.popleft()
        else:
            if len(rgb_history) > 0:
                rgb_history.popleft()
        
        success, buffer = cv2.imencode('.jpg', bgr_frame)
        if not success:
            continue
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Deteção de Cores - OV5647</title>
            <script>
                // Atualizar o painel lateral automaticamente a cada 200ms
                setInterval(async () => {
                    try {
                        let response = await fetch('/color_status');
                        let data = await response.json();
                        let box = document.getElementById('color-box');
                        let text = document.getElementById('color-name');
                        
                        text.innerText = data.name;
                        box.style.backgroundColor = `rgb(${data.rgb[0]}, ${data.rgb[1]}, ${data.rgb[2]})`;
                    } catch (e) {
                        console.log("Erro ao atualizar estado");
                    }
                }, 200);
            </script>
        </head>
        <body style="background-color: #18181b; color: white; font-family: sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center;">
            <h1 style="margin-bottom: 20px;">Deteção de Cores em Direto (OV5647)</h1>
            
            <div style="display: flex; gap: 20px; align-items: flex-start; max-width: 1600px; width: 100%; justify-content: center;">
                <!-- Feed de Vídeo -->
                <div style="flex: 3; text-align: center;">
                    <img src="/video_feed" style="width: 100%; max-width: 1100px; height: auto; border: 2px solid #3f3f46; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);" />
                </div>
                
                <!-- Pop-up / Painel Lateral ao lado do ecrã -->
                <div style="flex: 1; background-color: #27272a; border: 2px solid #3f3f46; border-radius: 12px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); min-width: 250px; text-align: center;">
                    <h3 style="margin-top: 0; color: #a1a1aa; text-transform: uppercase; font-size: 14px; letter-spacing: 1px;">Cor Detetada</h3>
                    
                    <!-- Caixa de Amostra de Cor -->
                    <div id="color-box" style="width: 100px; height: 100px; margin: 20px auto; border-radius: 50%; border: 4px solid white; background-color: #71717a; transition: background-color 0.3s ease;"></div>
                    
                    <!-- Nome da Cor -->
                    <h2 id="color-name" style="font-size: 24px; margin: 15px 0 5px 0; font-weight: bold;">A procurar...</h2>
                </div>
            </div>
        </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/color_status')
def color_status():
    """Rota secundária para enviar a cor atual em JSON para o pop-up lateral."""
    return jsonify({
        "name": current_detected_color["name"],
        "rgb": current_detected_color["rgb"]
    })

if __name__ == '__main__':
    try:
        print("Servidor com painel lateral iniciado! Acede a http://<ip-do-pi>:5000")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        picam2.stop()