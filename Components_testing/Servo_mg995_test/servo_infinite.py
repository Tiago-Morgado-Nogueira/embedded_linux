import time
from gpiozero import Servo

# Definir os pinos GPIO do Raspberry Pi (Muda conforme as tuas ligações físicas)
PIN_MG995_1 = 17
PIN_MG995_2 = 18
PIN_SG90 = 27

# Inicializar os servos com os limites de pulso padrão (0.5ms a 2.5ms)
# O gpiozero aceita valores de -1.0 (0°) a 1.0 (180°)
servo_mg1 = Servo(PIN_MG995_1, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)
servo_mg2 = Servo(PIN_MG995_2, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)
servo_sg90 = Servo(PIN_SG90, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

print("=== Teste Contínuo de Servos Iniciado ===")
print("A mover os 3 servos continuamente. Pressiona Ctrl+C para parar.")

try:
    while True:
        # 1. Ir gradualmente de -1.0 (0°) até 1.0 (180°)
        for i in range(-10, 11):
            val = i / 10.0
            servo_mg1.value = val
            servo_mg2.value = val
            servo_sg90.value = val
            time.sleep(0.04) # Ajusta a velocidade alterando este tempo
            
        # 2. Voltar gradualmente de 1.0 (180°) até -1.0 (0°)
        for i in range(10, -11, -1):
            val = i / 10.0
            servo_mg1.value = val
            servo_mg2.value = val
            servo_sg90.value = val
            time.sleep(0.04)

except KeyboardInterrupt:
    print("\nTeste terminado pelo utilizador. A libertar os servos...")
    servo_mg1.detach()
    servo_mg2.detach()
    servo_sg90.detach()
