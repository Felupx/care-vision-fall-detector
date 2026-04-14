import cv2
from cvzone.PoseModule import PoseDetector

def main():
    # 1. Configuração Inicial
    # Troque pelo caminho do seu vídeo ou coloque 0 para usar a webcam
    video_path = "../data/vd01.mp4" 
    cap = cv2.VideoCapture(video_path)
    
    # Inicializa o detector do MediaPipe via cvzone
    detector = PoseDetector()

    while True:
        sucesso, img = cap.read()
        if not sucesso:
            break # Fim do vídeo

        # Redimensiona para padronizar a análise e deixar o processamento mais leve
        img = cv2.resize(img, (1280, 720))

        # 2. Detecção de Pose
        img = detector.findPose(img)
        lmList, bboxInfo = detector.findPosition(img, draw=False)

        # 3. Lógica de Identificação de Queda (Base inicial)
        if lmList:
            # Pegando as coordenadas Y (índice 1) da cabeça (ponto 0) e joelho (ponto 26)
            y_cabeca = lmList[0][1]
            y_joelho = lmList[26][1]
            
            # Cálculo básico: cabeça abaixo ou na mesma linha do joelho
            diferenca = y_joelho - y_cabeca
            
            if diferenca <= 0:
                # Dispara o alerta visual na tela
                if bboxInfo:
                    x, y, w, h = bboxInfo["bbox"]
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)
                    cv2.putText(img, "QUEDA DETECTADA", (x, y - 30), 
                                cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)

        # Exibe a imagem
        cv2.imshow("Monitoramento de Quedas - UPX", img)
        
        # Pressione 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()