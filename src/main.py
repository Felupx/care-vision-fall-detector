from pathlib import Path

import cv2
from cvzone.PoseModule import PoseDetector


VIDEO_FILE = "vd01.mp4"
FRAME_SIZE = (1280, 720)
FALL_CONFIRMATION_FRAMES = 8
TORSO_RATIO_THRESHOLD = 0.60


def get_video_source():
    base_dir = Path(__file__).resolve().parent.parent
    return str(base_dir / "data" / VIDEO_FILE)


def is_fall_detected(landmarks, bbox_info):
    if not bbox_info:
        return False

    # Cada landmark vem no formato [id, x, y, z, visibility].
    head_y = landmarks[0][2]
    left_hip_y = landmarks[23][2]
    right_hip_y = landmarks[24][2]
    left_knee_y = landmarks[25][2]
    right_knee_y = landmarks[26][2]

    hip_y = (left_hip_y + right_hip_y) / 2
    knee_y = (left_knee_y + right_knee_y) / 2

    x, y, w, h = bbox_info["bbox"]
    width_height_ratio = w / max(h, 1)

    torso_height = abs(hip_y - head_y)
    lower_body_height = max(abs(knee_y - hip_y), 1)
    torso_ratio = torso_height / lower_body_height

    return width_height_ratio > 1.1 or torso_ratio < TORSO_RATIO_THRESHOLD


def draw_status(img, bbox_info, fall_frames):
    if not bbox_info:
        return

    x, y, w, h = bbox_info["bbox"]
    is_confirmed_fall = fall_frames >= FALL_CONFIRMATION_FRAMES
    color = (0, 0, 255) if is_confirmed_fall else (0, 255, 255)
    label = "QUEDA DETECTADA" if is_confirmed_fall else "Monitorando risco"

    cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
    cv2.putText(
        img,
        label,
        (x, max(y - 20, 30)),
        cv2.FONT_HERSHEY_PLAIN,
        2.5,
        color,
        3,
    )


def main():
    # Troque para 0 se quiser usar a webcam.
    video_source = get_video_source()
    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        raise FileNotFoundError(f"Nao foi possivel abrir a fonte de video: {video_source}")

    detector = PoseDetector()
    fall_frames = 0

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.resize(img, FRAME_SIZE)

        img = detector.findPose(img)
        landmarks, bbox_info = detector.findPosition(img, draw=False)

        if landmarks and len(landmarks) > 26:
            if is_fall_detected(landmarks, bbox_info):
                fall_frames += 1
            else:
                fall_frames = 0

            if fall_frames > 0:
                draw_status(img, bbox_info, fall_frames)
        else:
            fall_frames = 0

        cv2.imshow("Monitoramento de Quedas - UPX", img)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
