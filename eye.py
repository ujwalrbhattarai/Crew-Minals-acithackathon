import cv2
import mediapipe as mp
import numpy as np
import time
from collections import deque

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

LEFT_EYE_IDX = [33, 133]
RIGHT_EYE_IDX = [362, 263]
LEFT_IRIS_IDX = 468
RIGHT_IRIS_IDX = 473

cap = cv2.VideoCapture(0)
violation_counter = 0

CALIBRATION_DURATION = 5  # seconds

# Fixed tolerance band (adjust if needed)
HORIZONTAL_TOL = 0.08
VERTICAL_TOL = 0.08

# --- smoothing (moving average) ---
SMOOTHING_WINDOW = 5
dx_buffer, dy_buffer = deque(maxlen=SMOOTHING_WINDOW), deque(maxlen=SMOOTHING_WINDOW)

# --- dwell detection ---
OUTSIDE_FRAMES_REQUIRED = 10
outside_frame_count = 0

def get_gaze_offset(landmarks, eye_indices, iris_idx, image_w, image_h):
    eye_left = np.array([landmarks[eye_indices[0]].x * image_w,
                         landmarks[eye_indices[0]].y * image_h])
    eye_right = np.array([landmarks[eye_indices[1]].x * image_w,
                          landmarks[eye_indices[1]].y * image_h])

    eye_center = (eye_left + eye_right) / 2.0
    iris = np.array([landmarks[iris_idx].x * image_w,
                     landmarks[iris_idx].y * image_h])

    eye_width = np.linalg.norm(eye_right - eye_left)
    eye_height = eye_width / 2  # approximate

    dx = (iris[0] - eye_center[0]) / eye_width
    dy = (iris[1] - eye_center[1]) / eye_height

    return dx, dy

# Calibration phase
start_time = time.time()
calibrated = False
horizontal_values = []
vertical_values = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    results = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark

        l_dx, l_dy = get_gaze_offset(landmarks, LEFT_EYE_IDX, LEFT_IRIS_IDX, w, h)
        r_dx, r_dy = get_gaze_offset(landmarks, RIGHT_EYE_IDX, RIGHT_IRIS_IDX, w, h)
        avg_dx = (l_dx + r_dx) / 2
        avg_dy = (l_dy + r_dy) / 2

        # Apply smoothing
        dx_buffer.append(avg_dx)
        dy_buffer.append(avg_dy)
        smooth_dx = np.mean(dx_buffer)
        smooth_dy = np.mean(dy_buffer)

        current_time = time.time()
        if not calibrated:
            horizontal_values.append(smooth_dx)
            vertical_values.append(smooth_dy)
            cv2.putText(frame, f'Calibrating... Look at screen center ({int(current_time - start_time)}s)',
                        (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

            if current_time - start_time >= CALIBRATION_DURATION:
                h_center = np.median(horizontal_values)
                v_center = np.median(vertical_values)
                calibrated = True
        else:
            # Check if gaze is outside zone with fixed tolerance
            if (abs(smooth_dx - h_center) > HORIZONTAL_TOL or
                abs(smooth_dy - v_center) > VERTICAL_TOL):
                outside_frame_count += 1
                if outside_frame_count >= OUTSIDE_FRAMES_REQUIRED:
                    violation_counter += 1
                    outside_frame_count = 0
                    cv2.putText(frame, f"Violation! ({violation_counter})", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            else:
                outside_frame_count = 0
                cv2.putText(frame, "Looking at Screen", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        # Debug info
        cv2.putText(frame, f"dx: {smooth_dx:.2f}, dy: {smooth_dy:.2f}", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        cv2.putText(frame, f"Violations: {violation_counter}", (w-300, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    else:
        cv2.putText(frame, "Eyes not detected", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)

    cv2.imshow('Automated Gaze Calibration', frame)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
