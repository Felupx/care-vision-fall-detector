import time
from pathlib import Path
import cv2
import cvzone
from cvzone.PoseModule import PoseDetector
import firebase_admin
from firebase_admin import credentials, firestore

# config firestore
FIREBASE_KEY = "database.json" 

cred = credentials.Certificate(FIREBASE_KEY)
firebase_admin.initialize_app(cred)
db = firestore.client()

doc_ref = db.collection("monitoramento_camera").document("estado_atual")

FRAME_SIZE = (1280, 720)

def main():
    video = cv2.VideoCapture(0)  # abre webcam notebook
    detector = PoseDetector()
    
    ultimo_status = None 
    tempo_simulacao = 0

    print("\n--- CONECTADO AO FIRESTORE (FLUTTERFLOW) ---")

    while True:
        check, img = video.read()
        if not check:
            break

        img = cv2.resize(img, FRAME_SIZE)
        img = detector.findPose(img)
        pontos, bbox = detector.findPosition(img, draw=False)

        status_atual = 0  # 0 = Estável

        # Tecla F para simular queda (debug)
        if time.time() < tempo_simulacao:
            status_atual = 1
            cvzone.putTextRect(img, "TESTE: SIMULANDO QUEDA", (50, 100), scale=3, colorR=(0, 0, 255))
        
        # IA calcula queda com base na diferença entre a cabeça e o joelho
        elif len(pontos) >= 1 and bbox:
            x, y, w, h = bbox["bbox"]
            cabeca = pontos[0][2]
            joelho = pontos[26][2]
            diferenca = joelho - cabeca

            if diferenca <= 0:
                status_atual = 1  # 1 = queda
                cvzone.putTextRect(img, "QUEDA DETECTADA", (x, y - 80), scale=3, colorR=(0, 0, 255))
            else:
                cvzone.putTextRect(img, "POSTURA ESTAVEL", (x, y - 80), scale=3, colorR=(0, 180, 0))

        # se o status atual for diferente do ultimo, ele envia pro firestore
        if status_atual != ultimo_status:
            try:
                doc_ref.set({"status_queda": status_atual}) 
                print(f"Firestore atualizado: {status_atual}")
                ultimo_status = status_atual
            except Exception as e:
                print(f"Erro Firestore: {e}")

        cv2.imshow("IMG", img)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla in (ord("q"), 27):
            break
        elif tecla == ord("f"):
            tempo_simulacao = time.time() + 3

    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()