import cv2
from flask import Flask, Response
from picamera2 import Picamera2

app = Flask(__name__)

# Inicializar e configurar a câmara OV5647
picam2 = Picamera2()
camera_config = picam2.create_video_configuration(main={"size": (1280, 720)})
picam2.configure(camera_config)
picam2.start()

def generate_frames():
    """Gerador contínuo de fotogramas em formato JPEG para streaming."""
    while True:
        # Capturar o fotograma da câmara
        frame = picam2.capture_array()
        
        # Converter de RGB (Picamera2) para BGR
        success, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        if not success:
            continue
        
        frame_bytes = buffer.tobytes()
        
        # Produzir o fluxo no formato multipart/x-mixed-replace exigido pelo MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    """Página HTML simples que incorpora o fluxo de vídeo."""
    return """
    <html>
        <head>
            <title>Raspberry Pi - OV5647 Live Stream</title>
        </head>
        <body style="background-color: #222; color: white; text-align: center; font-family: sans-serif;">
            <h1>Transmissao em Direto - OV5647</h1>
            <div style="margin-top: 20px;">
                <img src="/video_feed" width="960" height="540" style="border: 2px solid #555; border-radius: 8px;" />
            </div>
        </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    """Rota que serve o fluxo contínuo de vídeo."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        print("Servidor web iniciado! Acede a http://192.168.137.171:5000 no teu browser.")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        picam2.stop()
