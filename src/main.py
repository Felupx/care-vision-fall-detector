import time
from pathlib import Path
import cv2
import cvzone
from cvzone.PoseModule import PoseDetector
import firebase_admin
from firebase_admin import credentials, db

# Configuração Firebase
FIREBASE_KEY = "database.json" 
URL_DATABASE = "https://care-vision-dc352-default-rtdb.firebaseio.com/"

cred = credentials.Certificate(FIREBASE_KEY)
firebase_admin.initialize_app(cred, {'databaseURL': URL_DATABASE})
status_ref = db.reference('status_queda')

FRAME_SIZE = (1280, 720)

def main():
    video = cv2.VideoCapture(0)  # Abre a webcam do notebook
    detector = PoseDetector()
    
    ultimo_status = None 
    tempo_simulacao = 0

    while True:
        check, img = video.read()
        if not check:
            break

        img = cv2.resize(img, FRAME_SIZE)
        img = detector.findPose(img)
        pontos, bbox = detector.findPosition(img, draw=False)

        status_atual = 0  # 0 = Estável

        # Se a tecla F for pressionada, força o status de queda por 3 segundos
        if time.time() < tempo_simulacao:
            status_atual = 1
            cvzone.putTextRect(img, "TESTE: SIMULANDO QUEDA", (50, 100), scale=3, colorR=(0, 0, 255))
        
        # Senão, segue a lógica da inteligência artificial
        elif len(pontos) >= 1 and bbox:
            x, y, w, h = bbox["bbox"]
            cabeca = pontos[0][2]
            joelho = pontos[26][2]
            diferenca = joelho - cabeca

            if diferenca <= 0:
                status_atual = 1  # 1 = Queda
                cvzone.putTextRect(img, "QUEDA DETECTADA", (x, y - 80), scale=3, colorR=(0, 0, 255))
            else:
                cvzone.putTextRect(img, "POSTURA ESTAVEL", (x, y - 80), scale=3, colorR=(0, 180, 0))

        # Envia para o Firebase apenas se o status mudar
        if status_atual != ultimo_status:
            try:
                status_ref.set({"status": status_atual}) 
                print(f"Firebase atualizado: {status_atual}")
                ultimo_status = status_atual
            except Exception as e:
                print(f"Erro Firebase: {e}")

        cv2.imshow("IMG", img)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla in (ord("q"), 27):  # Q ou ESC para sair
            break
        elif tecla == ord("f"):  # F para testar queda
            tempo_simulacao = time.time() + 3

    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()