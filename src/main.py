import argparse
import math
import time
from pathlib import Path
import cv2
import cvzone
from cvzone.PoseModule import PoseDetector

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
FIREBASE_KEY = str(BASE_DIR / "database.json")

FRAME_SIZE = (1280, 720)
FALL_CONFIRMATION_FRAMES = 8
RECOVERY_CONFIRMATION_FRAMES = 12
HEAD_KNEE_LINE_MARGIN_RATIO = 0.25
BODY_HORIZONTAL_RATIO = 1.15
LOW_BODY_RATIO = 0.55
GROUND_CONTACT_RATIO = 0.78
FAST_HIP_DROP_RATIO = 0.08
SPINE_HORIZONTAL_ANGLE = 60
SPINE_INCLINED_ANGLE = 35


def parse_args():
    parser = argparse.ArgumentParser(description="Detector de quedas Care Vision")
    parser.add_argument(
        "--video",
        help="Nome do video dentro da pasta data/ ou caminho completo para o arquivo.",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Indice da camera usada quando --video nao for informado.",
    )
    return parser.parse_args()


def conectar_firestore():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred = credentials.Certificate(FIREBASE_KEY)
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        print("\n--- CONECTADO AO FIRESTORE (FLUTTERFLOW) ---")
        return db.collection("monitoramento_camera").document("estado_atual")
    except Exception as e:
        print(f"\nFirestore indisponivel, rodando apenas localmente: {e}")
        return None


def criar_fonte_video(args):
    if not args.video:
        return args.camera

    caminho_video = Path(args.video)
    if caminho_video.is_absolute():
        return str(caminho_video)

    if caminho_video.exists():
        return str(caminho_video)

    caminho_projeto = PROJECT_DIR / caminho_video
    if caminho_projeto.exists():
        return str(caminho_projeto)

    return str(DATA_DIR / caminho_video)


def ponto_medio(pontos, indice_a, indice_b):
    return (
        (pontos[indice_a][0] + pontos[indice_b][0]) / 2,
        (pontos[indice_a][1] + pontos[indice_b][1]) / 2,
    )


def calcular_coluna(pontos):
    ombro_centro = ponto_medio(pontos, 11, 12)
    quadril_centro = ponto_medio(pontos, 23, 24)

    dx = quadril_centro[0] - ombro_centro[0]
    dy = quadril_centro[1] - ombro_centro[1]
    if dx == 0 and dy == 0:
        return None

    angulo_vertical = math.degrees(math.atan2(abs(dx), abs(dy)))
    return {
        "ombro": ombro_centro,
        "quadril": quadril_centro,
        "angulo_vertical": angulo_vertical,
    }


def desenhar_coluna(img, coluna, suspeita_queda):
    if not coluna:
        return

    angulo = coluna["angulo_vertical"]
    if suspeita_queda or angulo >= SPINE_HORIZONTAL_ANGLE:
        cor = (0, 0, 255)
    elif angulo >= SPINE_INCLINED_ANGLE:
        cor = (0, 170, 255)
    else:
        cor = (0, 180, 0)

    ombro = tuple(map(int, coluna["ombro"]))
    quadril = tuple(map(int, coluna["quadril"]))
    texto_pos = (ombro[0], max(35, ombro[1] - 25))

    cv2.line(img, ombro, quadril, cor, 4)
    cv2.circle(img, ombro, 6, cor, cv2.FILLED)
    cv2.circle(img, quadril, 6, cor, cv2.FILLED)
    cvzone.putTextRect(
        img,
        f"COLUNA {angulo:.0f} deg",
        texto_pos,
        scale=1.4,
        thickness=2,
        colorR=cor,
    )


def analisar_pose(pontos, bbox, altura_frame, quadril_anterior=None):
    if len(pontos) <= 28 or not bbox:
        return False, (50, 100), None, None

    x, y, w, h = bbox["bbox"]
    if h <= 0:
        return False, (50, 100), None, None

    cabeca_y = pontos[0][1]
    joelho_y = (pontos[25][1] + pontos[26][1]) / 2
    quadril_y = (pontos[23][1] + pontos[24][1]) / 2
    coluna = calcular_coluna(pontos)

    distancia_vertical_cabeca_ate_joelho = joelho_y - cabeca_y
    margem_linha_joelho = h * HEAD_KNEE_LINE_MARGIN_RATIO
    proporcao_corpo = w / h
    base_corpo = y + h

    cabeca_na_altura_do_joelho_ou_abaixo = (
        distancia_vertical_cabeca_ate_joelho <= margem_linha_joelho
    )
    corpo_horizontal = proporcao_corpo >= BODY_HORIZONTAL_RATIO
    coluna_horizontal = (
        coluna is not None
        and coluna["angulo_vertical"] >= SPINE_HORIZONTAL_ANGLE
    )
    quadril_baixo = quadril_y >= altura_frame * LOW_BODY_RATIO
    corpo_proximo_chao = base_corpo >= altura_frame * GROUND_CONTACT_RATIO
    queda_rapida = (
        quadril_anterior is not None
        and quadril_y - quadril_anterior >= altura_frame * FAST_HIP_DROP_RATIO
    )

    postura_de_queda = (
        coluna_horizontal
        or corpo_horizontal
        or cabeca_na_altura_do_joelho_ou_abaixo
    )
    corpo_baixo = quadril_baixo or corpo_proximo_chao
    suspeita = (postura_de_queda and corpo_baixo) or (
        queda_rapida and (postura_de_queda or corpo_baixo)
    )

    return suspeita, (x, max(50, y - 80)), quadril_y, coluna


def atualizar_firestore(doc_ref, status_atual, ultimo_status):
    if doc_ref is None:
        return ultimo_status

    if status_atual != ultimo_status:
        try:
            dados = {
                "status_queda": status_atual,
                "ultima_atualizacao": time.time()  # Timestamp para o app saber quando mudou
            }
            doc_ref.set(dados, merge=True)
            print(f"Firestore atualizado (Mudança de Estado): {status_atual}")
            return status_atual
        except Exception as e:
            print(f"Erro Firestore: {e}")
            return ultimo_status
            
    elif status_atual == 1:
        agora = time.time()
        if not hasattr(atualizar_firestore, "ultimo_pulso") or (agora - atualizar_firestore.ultimo_pulso > 5):
            atualizar_firestore.ultimo_pulso = agora
            try:
                doc_ref.set({"alerta_continuo_timestamp": agora}, merge=True)
                print("Firestore atualizado: Alerta contínuo de queda pendente.")
            except Exception as e:
                print(f"Erro no pulso do Firestore: {e}")

    return ultimo_status


def main():
    args = parse_args()
    fonte_video = criar_fonte_video(args)
    video = cv2.VideoCapture(fonte_video)
    if not video.isOpened():
        print(f"Erro: nao foi possivel abrir a fonte de video: {fonte_video}")
        return

    detector = PoseDetector()
    doc_ref = conectar_firestore()

    ultimo_status_enviado = None
    status_confirmado = 0
    frames_suspeitos = 0
    frames_estaveis = 0
    quadril_anterior = None
    tempo_simulacao = 0

    fps = video.get(cv2.CAP_PROP_FPS)
    delay = max(1, int(1000 / fps)) if fps and fps > 1 else 1

    while True:
        check, img = video.read()
        if not check:
            break

        img = cv2.resize(img, FRAME_SIZE)
        img = detector.findPose(img)
        pontos, bbox = detector.findPosition(img, draw=False)

        suspeita_queda, posicao_texto, quadril_atual, coluna = analisar_pose(
            pontos,
            bbox,
            FRAME_SIZE[1],
            quadril_anterior,
        )
        quadril_anterior = quadril_atual

        simulando_queda = time.time() < tempo_simulacao
        if simulando_queda:
            suspeita_queda = True
            posicao_texto = (50, 100)

        desenhar_coluna(img, coluna, suspeita_queda)

        if suspeita_queda:
            frames_suspeitos += 1
            frames_estaveis = 0
        else:
            frames_suspeitos = 0
            frames_estaveis += 1

        if frames_suspeitos >= FALL_CONFIRMATION_FRAMES:
            status_confirmado = 1
        elif status_confirmado == 1 and frames_estaveis >= RECOVERY_CONFIRMATION_FRAMES:
            status_confirmado = 0

        if simulando_queda:
            texto = "TESTE: SIMULANDO QUEDA"
            cor = (0, 0, 255)
        elif status_confirmado == 1:
            texto = "QUEDA CONFIRMADA"
            cor = (0, 0, 255)
        elif frames_suspeitos > 0:
            texto = f"RISCO DE QUEDA {frames_suspeitos}/{FALL_CONFIRMATION_FRAMES}"
            cor = (0, 170, 255)
        elif len(pontos) <= 28 or not bbox:
            texto = "SEM POSE DETECTADA"
            cor = (90, 90, 90)
        else:
            texto = "POSTURA ESTAVEL"
            cor = (0, 180, 0)

        cvzone.putTextRect(img, texto, posicao_texto, scale=3, colorR=cor)

        ultimo_status_enviado = atualizar_firestore(
            doc_ref,
            status_confirmado,
            ultimo_status_enviado,
        )

        cv2.imshow("IMG", img)

        tecla = cv2.waitKey(delay) & 0xFF
        if tecla in (ord("q"), 27):
            break
        elif tecla == ord("f"):
            tempo_simulacao = time.time() + 3

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
