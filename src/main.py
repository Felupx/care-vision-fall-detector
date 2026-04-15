from pathlib import Path

import cv2
import cvzone
from cvzone.PoseModule import PoseDetector


VIDEO_FILE = "vd01.mp4"
FRAME_SIZE = (1280, 720)


def get_video_path():
    base_dir = Path(__file__).resolve().parent.parent
    return str(base_dir / "data" / VIDEO_FILE)


def main():
    video = cv2.VideoCapture(get_video_path())
    detector = PoseDetector()

    while True:
        check, img = video.read()
        if not check:
            break

        img = cv2.resize(img, FRAME_SIZE)
        img = detector.findPose(img)
        pontos, bbox = detector.findPosition(img, draw=False)

        if len(pontos) >= 1 and bbox:
            x, y, w, h = bbox["bbox"]
            cabeca = pontos[0][2]
            joelho = pontos[26][2]
            diferenca = joelho - cabeca

            if diferenca <= 0:
                cvzone.putTextRect(
                    img,
                    "QUEDA DETECTADA",
                    (x, y - 80),
                    scale=3,
                    thickness=3,
                    colorR=(0, 0, 255),
                )
            else:
                cvzone.putTextRect(
                    img,
                    "POSTURA ESTAVEL",
                    (x, y - 80),
                    scale=3,
                    thickness=3,
                    colorR=(0, 180, 0),
                )

        cv2.imshow("IMG", img)

        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
