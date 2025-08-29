import cv2
import mediapipe as mp
import numpy as np
import time
import pyaudio
from collections import deque

# ===================== Setup =====================
# Face/Eye Tracking
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

LEFT_EYE_IDX = [33, 133]
RIGHT_EYE_IDX = [362, 263]
LEFT_IRIS_IDX = 468
RIGHT_IRIS_IDX = 473

# Tolerances
CALIBRATION_DURATION = 5  # seconds
HORIZONTAL_TOL = 0.06
VERTICAL_TOL = 0.06
HEAD_TOL = 60         # reduced from 80 px → stricter
HEAD_ANGLE_TOL = 2    # degrees

# Smoothing
SMOOTHING_WINDOW = 5
dx_buffer, dy_buffer = deque(maxlen=SMOOTHING_WINDOW), deque(maxlen=SMOOTHING_WINDOW)

# Dwell detection
OUTSIDE_FRAMES_REQUIRED = 10
outside_eye_frame_count = 0
outside_head_frame_count = 0

# Violation counters
eye_violation_counter = 0
head_violation_counter = 0
sound_violation_counter = 0

# Sound Monitoring
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
MAX_RMS = 1200
THRESHOLD = 500

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                input=True, frames_per_buffer=CHUNK)

# Camera
cap = cv2.VideoCapture(0)


# ===================== Functions =====================
def get_gaze_offset(landmarks, eye_indices, iris_idx, image_w, image_h):
    """Compute normalized gaze offset for one eye."""
    eye_left = np.array([landmarks[eye_indices[0]].x * image_w,
                         landmarks[eye_indices[0]].y * image_h])
    eye_right = np.array([landmarks[eye_indices[1]].x * image_w,
                          landmarks[eye_indices[1]].y * image_h])
    eye_center = (eye_left + eye_right) / 2.0
    iris = np.array([landmarks[iris_idx].x * image_w,
                     landmarks[iris_idx].y * image_h])

    eye_width = np.linalg.norm(eye_right - eye_left)
    eye_height = eye_width / 2
    dx = (iris[0] - eye_center[0]) / eye_width
    dy = (iris[1] - eye_center[1]) / eye_height
    return dx, dy


# ===================== Main Loop =====================
start_time = time.time()
calibrated = False
horizontal_values = []
vertical_values = []

try:
    while cap.isOpened():
        # -------- Audio --------
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
        except Exception:
            audio_data = np.array([0], dtype=np.int16)

        if audio_data.size > 0:
            rms_val = np.sqrt(np.mean(np.square(audio_data.astype(np.float64))))
            rms = 0 if np.isnan(rms_val) or np.isinf(rms_val) else rms_val
        else:
            rms = 0

        if rms > THRESHOLD:
            sound_violation_counter += 1

        # -------- Video --------
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        results = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            # Eye tracking
            l_dx, l_dy = get_gaze_offset(landmarks, LEFT_EYE_IDX, LEFT_IRIS_IDX, w, h)
            r_dx, r_dy = get_gaze_offset(landmarks, RIGHT_EYE_IDX, RIGHT_IRIS_IDX, w, h)
            avg_dx, avg_dy = (l_dx + r_dx) / 2, (l_dy + r_dy) / 2

            dx_buffer.append(avg_dx)
            dy_buffer.append(avg_dy)
            smooth_dx, smooth_dy = np.mean(dx_buffer), np.mean(dy_buffer)

            # Nose position
            nose = landmarks[1]
            nose_x, nose_y = int(nose.x * w), int(nose.y * h)
            center_x, center_y = w // 2, h // 2

            # Calibration
            current_time = time.time()
            if not calibrated:
                horizontal_values.append(smooth_dx)
                vertical_values.append(smooth_dy)
                cv2.putText(frame, f'Calibrating... ({int(current_time - start_time)}s)',
                            (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
                if current_time - start_time >= CALIBRATION_DURATION:
                    h_center = np.median(horizontal_values)
                    v_center = np.median(vertical_values)
                    calibrated = True
            else:
                # Eye violation
                if (abs(smooth_dx - h_center) > HORIZONTAL_TOL or
                        abs(smooth_dy - v_center) > VERTICAL_TOL):
                    outside_eye_frame_count += 1
                    if outside_eye_frame_count >= OUTSIDE_FRAMES_REQUIRED:
                        eye_violation_counter += 1
                        outside_eye_frame_count = 0
                else:
                    outside_eye_frame_count = 0

                # Head violation (position)
                if np.linalg.norm([nose_x - center_x, nose_y - center_y]) > HEAD_TOL:
                    outside_head_frame_count += 1
                    if outside_head_frame_count >= OUTSIDE_FRAMES_REQUIRED:
                        head_violation_counter += 1
                        outside_head_frame_count = 0
                else:
                    outside_head_frame_count = max(0, outside_head_frame_count - 1)

                # Head angle
                left_eye = np.array([landmarks[LEFT_EYE_IDX[0]].x * w,
                                     landmarks[LEFT_EYE_IDX[0]].y * h])
                right_eye = np.array([landmarks[RIGHT_EYE_IDX[0]].x * w,
                                      landmarks[RIGHT_EYE_IDX[0]].y * h])
                eye_vector = right_eye - left_eye
                head_angle = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))
                if abs(head_angle) > HEAD_ANGLE_TOL:
                    outside_head_frame_count += 1
                    if outside_head_frame_count >= OUTSIDE_FRAMES_REQUIRED:
                        head_violation_counter += 1
                        outside_head_frame_count = 0

                # Debug info
                cv2.putText(frame, f"Head Angle: {head_angle:.2f} deg", (50, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            # Draw reference markers
            cv2.circle(frame, (nose_x, nose_y), 5, (255, 255, 0), -1)
            cv2.circle(frame, (center_x, center_y), 5, (0, 255, 255), -1)
        else:
            cv2.putText(frame, "Eyes not detected", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

        # -------- Sound bar overlay --------
        bar_height, bar_width = 200, 30
        x, y = 50, 200
        filled_height = int(min(rms / MAX_RMS, 1.0) * bar_height)

        if filled_height < bar_height * 0.33:
            color = (0, 255, 0)
        elif filled_height < bar_height * 0.66:
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)

        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (50, 50, 50), 2)
        cv2.rectangle(frame, (x, y + bar_height - filled_height),
                      (x + bar_width, y + bar_height), color, -1)

        # -------- Unified violation summary --------
        cv2.putText(frame, f"Eye: {eye_violation_counter}", (w-250, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(frame, f"Head: {head_violation_counter}", (w-250, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.putText(frame, f"Sound: {sound_violation_counter}", (w-250, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 128, 255), 2)

        # -------- Show --------
        cv2.imshow('Eye/Head & Sound Monitoring', frame)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    stream.stop_stream()
    stream.close()
    p.terminate()
