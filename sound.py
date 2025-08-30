import cv2
import pyaudio
import numpy as np

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
MAX_RMS = 1200  # Reduced for higher sensitivity
THRESHOLD = 5  # RMS threshold for violation

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

# Initialize OpenCV
cap = cv2.VideoCapture(0)
sound_violation_counter = 0

try:
    while True:
        # Read audio data
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
        except Exception as e:
            audio_data = np.array([0], dtype=np.int16)

        # Calculate RMS safely
        if audio_data.size == 0:
            rms = 0
        else:
            rms_val = np.sqrt(np.mean(np.square(audio_data.astype(np.float64))))
            rms = 0 if np.isnan(rms_val) or np.isinf(rms_val) else rms_val

        # Violation detection
        if rms > THRESHOLD:
            sound_violation_counter += 1

        # Read camera frame
        ret, frame = cap.read()
        if not ret:
            break

        # Draw analog loudness bar
        bar_height = 200  # decreased height
        bar_width = 30    # decreased width
        x = 50
        y = 50

        # Map RMS to bar height
        filled_height = int(min(rms / MAX_RMS, 1.0) * bar_height)

        # Determine color based on loudness
        if filled_height < bar_height * 0.33:
            color = (0, 255, 0)  # Green
        elif filled_height < bar_height * 0.66:
            color = (0, 255, 255)  # Yellow
        else:
            color = (0, 0, 255)  # Red

        # Draw the empty bar background
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (50, 50, 50), 2)

        # Draw the filled portion
        cv2.rectangle(frame, (x, y + bar_height - filled_height),
                      (x + bar_width, y + bar_height), color, -1)

        # Optional: draw border
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (255, 255, 255), 1)

        # Show violation count above bar
        cv2.putText(frame, f'Violations: {sound_violation_counter}', (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Display webcam feed
        cv2.imshow('Webcam with Loudness Meter', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    stream.stop_stream()
    stream.close()
    p.terminate()
