import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import json
import os
import threading
import time

class ProctorYApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ProctorY - Smart Exam Proctoring")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0f172a")
        self.root.resizable(True, True)
        
        # Modern color scheme
        self.colors = {
            "bg_primary": "#0f172a",    # Dark slate
            "bg_secondary": "#1e293b",  # Lighter slate
            "accent": "#3b82f6",        # Blue
            "success": "#10b981",       # Green
            "warning": "#f59e0b",       # Amber
            "danger": "#ef4444",        # Red
            "text_primary": "#f8fafc",  # White
            "text_secondary": "#cbd5e1" # Light gray
        }
        
        # State
        self.slides = []
        self.current_slide = 0
        self.questions = []
        self.answers = {}
        self.bookmarked_questions = set()
        self.exam_duration = 30 * 60  # 30 minutes in seconds
        self.time_remaining = self.exam_duration
        self.timer_running = False
        self.timer_thread = None
        self.monitoring_windows = {}  # Track open monitoring windows
        
        # Load content
        self.load_slides("slides")
        self.load_questions()
        
        # Start with slide presentation or exam based on content availability
        if self.slides:
            self.show_slide()
        elif self.questions:
            self.show_begin_exam()
        else:
            self.show_no_content()

    # ============================
    # CONTENT LOADING
    # ============================
    def load_slides(self, folder):
        """Load presentation slides from folder"""
        if os.path.exists(folder):
            for file in sorted(os.listdir(folder)):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    self.slides.append(os.path.join(folder, file))

    def load_questions(self):
        """Load questions from JSON file"""
        if os.path.exists("questions.json"):
            try:
                with open("questions.json", "r") as f:
                    self.questions = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.questions = []

    # ============================
    # UI COMPONENTS
    # ============================
    def create_header(self, title, subtitle=""):
        """Create modern header with title and optional subtitle"""
        header_frame = tk.Frame(self.root, bg=self.colors["bg_primary"], height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text=title, 
                              font=("Arial", 24, "bold"),
                              bg=self.colors["bg_primary"], 
                              fg=self.colors["text_primary"])
        title_label.pack(pady=(15, 0))
        
        if subtitle:
            subtitle_label = tk.Label(header_frame, text=subtitle,
                                    font=("Arial", 12),
                                    bg=self.colors["bg_primary"],
                                    fg=self.colors["text_secondary"])
            subtitle_label.pack()

    def create_button(self, parent, text, command, style="primary", width=20):
        """Create modern styled button"""
        color_map = {
            "primary": (self.colors["accent"], "white"),
            "success": (self.colors["success"], "white"),
            "warning": (self.colors["warning"], "white"),
            "danger": (self.colors["danger"], "white")
        }
        
        bg, fg = color_map.get(style, color_map["primary"])
        
        btn = tk.Button(parent, text=text, command=command,
                       font=("Arial", 12, "bold"),
                       bg=bg, fg=fg,
                       relief="flat", bd=0,
                       width=width, height=2,
                       cursor="hand2")
        
        # Hover effects
        def on_enter(e):
            btn.config(bg=self.lighten_color(bg))
        def on_leave(e):
            btn.config(bg=bg)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def lighten_color(self, color):
        """Simple color lightening for hover effects"""
        color_variants = {
            self.colors["accent"]: "#60a5fa",
            self.colors["success"]: "#34d399",
            self.colors["warning"]: "#fbbf24",
            self.colors["danger"]: "#f87171"
        }
        return color_variants.get(color, color)

    def create_exam_layout(self):
        """Create the main exam layout with video feed area"""
        # Main content frame (75% width)
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        self.main_frame.place(relx=0, rely=0, relwidth=0.75, relheight=1)
        
        # Right panel for video feed and monitoring (25% width)
        self.monitor_frame = tk.Frame(self.root, bg=self.colors["bg_secondary"])
        self.monitor_frame.place(relx=0.75, rely=0, relwidth=0.25, relheight=1)
        
        # Timer at top of monitor panel
        self.timer_frame = tk.Frame(self.monitor_frame, bg=self.colors["bg_secondary"])
        self.timer_frame.pack(fill="x", padx=10, pady=10)
        
        timer_label = tk.Label(self.timer_frame, text="Time Remaining",
                              font=("Arial", 12, "bold"),
                              bg=self.colors["bg_secondary"],
                              fg=self.colors["text_secondary"])
        timer_label.pack()
        
        self.timer_display = tk.Label(self.timer_frame, text="30:00",
                                     font=("Arial", 20, "bold"),
                                     bg=self.colors["bg_secondary"],
                                     fg=self.colors["warning"])
        self.timer_display.pack()
        

    def create_exam_layout(self):
        """Create the main exam layout with video feed area"""
        # Main content frame (75% width)
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        self.main_frame.place(relx=0, rely=0, relwidth=0.75, relheight=1)
        # Right panel for video feed and monitoring (25% width)
        self.monitor_frame = tk.Frame(self.root, bg=self.colors["bg_secondary"])
        self.monitor_frame.place(relx=0.75, rely=0, relwidth=0.25, relheight=1)
        # Timer at top of monitor panel
        self.timer_frame = tk.Frame(self.monitor_frame, bg=self.colors["bg_secondary"])
        self.timer_frame.pack(fill="x", padx=10, pady=10)
        timer_label = tk.Label(self.timer_frame, text="Time Remaining",
                              font=("Arial", 12, "bold"),
                              bg=self.colors["bg_secondary"],
                              fg=self.colors["text_secondary"])
        timer_label.pack()
        self.timer_display = tk.Label(self.timer_frame, text="30:00",
                                     font=("Arial", 20, "bold"),
                                     bg=self.colors["bg_secondary"],
                                     fg=self.colors["warning"])
        self.timer_display.pack()

        # Monitoring controls (Top row of right panel)
        controls_frame = tk.Frame(self.monitor_frame, bg=self.colors["bg_secondary"])
        controls_frame.pack(fill="x", padx=5, pady=(0, 5))
        tk.Label(controls_frame, text="🔧 Monitor Controls",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_secondary"]).pack()
        btn_frame = tk.Frame(controls_frame, bg=self.colors["bg_secondary"])
        btn_frame.pack(fill="x", pady=5)
        # Add buttons for each script
        script_buttons = [
            ("Devices", self.show_devices_monitor),
            ("Network", self.show_network_monitor),
            ("Background Apps", self.show_background_apps),
            ("Eye/Head Tracking", self.show_eyehead_tracking)
        ]
        for i, (text, cmd) in enumerate(script_buttons):
            btn = tk.Button(btn_frame, text=text, font=("Arial", 8),
                   bg=self.colors["accent"], fg="white",
                   relief="flat", bd=0, width=14, height=2,
                   command=cmd)
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Monitoring output area (Initially hidden)
        self.monitoring_output = tk.Frame(controls_frame, bg=self.colors["bg_primary"], height=100)
        self.monitoring_text = tk.Text(self.monitoring_output, font=("Consolas", 8),
                          bg=self.colors["bg_primary"], fg=self.colors["text_primary"],
                          relief="flat", bd=0, height=10, wrap="word")
        self.monitoring_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.close_monitor_btn = tk.Button(self.monitoring_output, text="✕ Close",
                          font=("Arial", 8), bg=self.colors["danger"],
                          fg="white", relief="flat", bd=0,
                          command=self.close_monitoring)
        self.close_monitor_btn.pack(pady=2)

        # Video feed area (Bottom row of right panel)
        self.video_frame = tk.Frame(self.monitor_frame, bg=self.colors["bg_primary"], relief="solid", bd=1)
        self.video_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        tk.Label(self.video_frame, text="📹 Live Video Feed",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg_primary"],
            fg=self.colors["text_secondary"]).pack(pady=5)
        self.video_label = tk.Label(self.video_frame, text="Click 'Eye/Head Tracking' to start",
                        font=("Arial", 9),
                        bg=self.colors["bg_primary"],
                        fg=self.colors["text_secondary"],
                        justify="center")
        self.video_label.pack(expand=True)
    # --- Script integration methods ---
    def show_devices_monitor(self):
        self.monitoring_output.pack(fill="x", pady=(5, 0))
        self.monitoring_text.delete(1.0, tk.END)
        try:
            import connectedperipherals
            devices = connectedperipherals.get_connected_peripherals()
            self.monitoring_text.insert(tk.END, "Connected Devices:\n" + "\n".join(devices))
        except Exception as e:
            self.monitoring_text.insert(tk.END, f"Error: {e}")

    def show_network_monitor(self):
        self.monitoring_output.pack(fill="x", pady=(5, 0))
        self.monitoring_text.delete(1.0, tk.END)
        try:
            import network
            conns = network.get_active_connections()
            lines = [f"{c['remote_ip']}:{c['remote_port']}" for c in conns]
            self.monitoring_text.insert(tk.END, "Active Connections:\n" + "\n".join(lines) if lines else "No active connections.")
        except Exception as e:
            self.monitoring_text.insert(tk.END, f"Error: {e}")

    def show_background_apps(self):
        self.monitoring_output.pack(fill="x", pady=(5, 0))
        self.monitoring_text.delete(1.0, tk.END)
        try:
            import back
            from io import StringIO
            import sys
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            back.list_background_applications()
            sys.stdout = old_stdout
            self.monitoring_text.insert(tk.END, mystdout.getvalue())
        except Exception as e:
            self.monitoring_text.insert(tk.END, f"Error: {e}")

    def show_eyehead_tracking(self):
        # Start a thread to run the OpenCV loop and update the video_label with frames
        if hasattr(self, '_eyehead_thread') and self._eyehead_thread.is_alive():
            return  # Already running
        self.video_label.config(text="Starting camera...")
        import threading
        self._eyehead_thread = threading.Thread(target=self._run_eyehead_tracking, daemon=True)
        self._eyehead_thread.start()

    def _run_eyehead_tracking(self):
        try:
            import cv2
            import mediapipe as mp
            import numpy as np
            from collections import deque
            mp_face_mesh = mp.solutions.face_mesh
            face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
            LEFT_EYE_IDX = [33, 133]
            RIGHT_EYE_IDX = [362, 263]
            LEFT_IRIS_IDX = 468
            RIGHT_IRIS_IDX = 473
            cap = cv2.VideoCapture(0)
            dx_buffer, dy_buffer = deque(maxlen=5), deque(maxlen=5)
            h_center = v_center = None
            calibrated = False
            horizontal_values = []
            vertical_values = []
            start_time = time.time()
            CALIBRATION_DURATION = 3
            HORIZONTAL_TOL = 0.06
            VERTICAL_TOL = 0.06
            HEAD_TOL = 80
            HEAD_ANGLE_TOL = 2
            OUTSIDE_FRAMES_REQUIRED = 10
            outside_eye_frame_count = 0
            outside_head_frame_count = 0
            eye_violation_counter = 0
            head_violation_counter = 0
            def get_gaze_offset(landmarks, eye_indices, iris_idx, image_w, image_h):
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
                    dx_buffer.append(avg_dx)
                    dy_buffer.append(avg_dy)
                    smooth_dx = np.mean(dx_buffer)
                    smooth_dy = np.mean(dy_buffer)
                    nose = landmarks[1]
                    nose_x, nose_y = int(nose.x * w), int(nose.y * h)
                    center_x, center_y = w // 2, h // 2
                    current_time = time.time()
                    if not calibrated:
                        horizontal_values.append(smooth_dx)
                        vertical_values.append(smooth_dy)
                        if current_time - start_time >= CALIBRATION_DURATION:
                            h_center = np.median(horizontal_values)
                            v_center = np.median(vertical_values)
                            calibrated = True
                        cv2.putText(frame, f'Calibrating... ({int(current_time - start_time)}s)',
                                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
                    else:
                        if (abs(smooth_dx - h_center) > HORIZONTAL_TOL or abs(smooth_dy - v_center) > VERTICAL_TOL):
                            outside_eye_frame_count += 1
                            if outside_eye_frame_count >= OUTSIDE_FRAMES_REQUIRED:
                                eye_violation_counter += 1
                                outside_eye_frame_count = 0
                        else:
                            outside_eye_frame_count = 0
                        if np.linalg.norm([nose_x - center_x, nose_y - center_y]) > HEAD_TOL:
                            outside_head_frame_count += 1
                            if outside_head_frame_count >= OUTSIDE_FRAMES_REQUIRED:
                                head_violation_counter += 1
                                outside_head_frame_count = 0
                        else:
                            outside_head_frame_count = max(0, outside_head_frame_count - 1)
                        left_eye = np.array([landmarks[LEFT_EYE_IDX[0]].x * w, landmarks[LEFT_EYE_IDX[0]].y * h])
                        right_eye = np.array([landmarks[RIGHT_EYE_IDX[0]].x * w, landmarks[RIGHT_EYE_IDX[0]].y * h])
                        eye_vector = right_eye - left_eye
                        head_angle = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))
                        head_x_min = int(min(left_eye[0], right_eye[0], nose_x))
                        head_x_max = int(max(left_eye[0], right_eye[0], nose_x))
                        head_y_min = int(min(left_eye[1], right_eye[1], nose_y))
                        head_y_max = int(max(left_eye[1], right_eye[1], nose_y))
                        cv2.rectangle(frame, (head_x_min, head_y_min), (head_x_max, head_y_max), (0, 255, 0), 2)
                        if abs(head_angle) > HEAD_ANGLE_TOL:
                            outside_head_frame_count += 1
                            if outside_head_frame_count >= OUTSIDE_FRAMES_REQUIRED:
                                head_violation_counter += 1
                                outside_head_frame_count = 0
                        else:
                            outside_head_frame_count = max(0, outside_head_frame_count - 1)
                        cv2.putText(frame, f"Head Angle: {head_angle:.2f} deg", (50, 120),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                        cv2.putText(frame, "Tracking...", (50, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 1)
                    cv2.putText(frame, f"dx:{smooth_dx:.2f} dy:{smooth_dy:.2f}", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                    cv2.putText(frame, f"Eye Violations: {eye_violation_counter}", (w-300, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 1)
                    cv2.putText(frame, f"Head Violations: {head_violation_counter}", (w-300, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 1)
                    cv2.circle(frame, (nose_x, nose_y), 5, (255,255,0), -1)
                    cv2.circle(frame, (center_x, center_y), 5, (0,255,255), -1)
                else:
                    cv2.putText(frame, "Eyes not detected", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 1)
                # Convert frame to Tkinter image and update video_label
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                from PIL import Image, ImageTk
                im = Image.fromarray(img)
                im = im.resize((320, 240))
                imgtk = ImageTk.PhotoImage(image=im)
                def update_img():
                    self.video_label.imgtk = imgtk
                    self.video_label.config(image=imgtk, text="")
                self.video_label.after(0, update_img)
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()
            def reset_img():
                self.video_label.config(image="", text="Click 'Eye/Head Tracking' to start")
            self.video_label.after(0, reset_img)
        except Exception as e:
            def show_err():
                self.video_label.config(image="", text=f"Error: {e}")
            self.video_label.after(0, show_err)
        
        # Status indicators at bottom
        status_frame = tk.Frame(self.monitor_frame, bg=self.colors["bg_secondary"])
        status_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(status_frame, text="System Status",
                font=("Arial", 9, "bold"),
                bg=self.colors["bg_secondary"],
                fg=self.colors["text_secondary"]).pack()
        
        self.status_labels = {}
        statuses = ["Face: ✓", "Network: ✓", "Focus: ✓"]
        for status in statuses:
            label = tk.Label(status_frame, text=status,
                           font=("Arial", 8),
                           bg=self.colors["bg_secondary"],
                           fg=self.colors["success"])
            label.pack()
            self.status_labels[status] = label

    # ============================
    # TIMER FUNCTIONALITY
    # ============================
    def start_timer(self):
        """Start the exam timer"""
        self.timer_running = True
        self.timer_thread = threading.Thread(target=self.timer_countdown, daemon=True)
        self.timer_thread.start()

    def timer_countdown(self):
        """Timer countdown logic"""
        while self.timer_running and self.time_remaining > 0:
            time.sleep(1)
            if self.timer_running:
                self.time_remaining -= 1
                self.update_timer_display()
        
        if self.time_remaining <= 0:
            self.root.after(0, self.time_up)

    def update_timer_display(self):
        """Update timer display"""
        if hasattr(self, 'timer_display'):
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            # Change color based on time remaining
            if self.time_remaining <= 300:  # Last 5 minutes
                color = self.colors["danger"]
            elif self.time_remaining <= 600:  # Last 10 minutes
                color = self.colors["warning"]
            else:
                color = self.colors["success"]
            
            self.timer_display.config(text=time_str, fg=color)

    def time_up(self):
        """Handle time up scenario"""
        self.timer_running = False
        messagebox.showinfo("Time Up", "Exam time has expired!")
        self.submit_exam()

    # ============================
    # SLIDE PRESENTATION
    # ============================
    def show_slide(self):
        """Display current slide"""
        self.clear_window()

        if self.current_slide < len(self.slides):
            self.create_header("ProctorY Presentation", f"Slide {self.current_slide + 1} of {len(self.slides)}")
            
            # Slide content frame
            content_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
            content_frame.pack(fill="both", expand=True, padx=40, pady=20)
            
            try:
                img = Image.open(self.slides[self.current_slide])
                # Maintain aspect ratio while fitting in frame
                img_width, img_height = img.size
                max_width, max_height = 800, 500
                ratio = min(max_width/img_width, max_height/img_height)
                new_size = (int(img_width * ratio), int(img_height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                tk_img = ImageTk.PhotoImage(img)
                
                img_label = tk.Label(content_frame, image=tk_img, bg=self.colors["bg_primary"])
                img_label.image = tk_img  # Keep reference
                img_label.pack(pady=20)
                
            except Exception as e:
                error_label = tk.Label(content_frame, text=f"Error loading slide: {str(e)}",
                                     font=("Arial", 16),
                                     bg=self.colors["bg_primary"],
                                     fg=self.colors["danger"])
                error_label.pack(pady=50)

            # Navigation
            nav_frame = tk.Frame(content_frame, bg=self.colors["bg_primary"])
            nav_frame.pack(pady=20)
            
            self.create_button(nav_frame, "Next Slide", self.next_slide).pack()
        else:
            self.show_begin_exam()

    def next_slide(self):
        """Move to next slide"""
        self.current_slide += 1
        self.show_slide()

    # ============================
    # EXAM FLOW
    # ============================
    def show_begin_exam(self):
        """Show begin exam screen"""
        self.clear_window()
        self.create_header("Ready to Begin", "All presentation materials completed")

        content_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        content_frame.pack(fill="both", expand=True)

        # Info card
        card_frame = tk.Frame(content_frame, bg=self.colors["bg_secondary"], 
                             relief="flat", bd=0)
        card_frame.pack(pady=80, padx=100, fill="x")

        tk.Label(card_frame, text="🎯 Demo Exam Ready",
                font=("Arial", 20, "bold"),
                bg=self.colors["bg_secondary"],
                fg=self.colors["text_primary"]).pack(pady=20)

        info_text = f"""• {len(self.questions)} questions available
• 30-minute time limit
• Full monitoring enabled
• No breaks allowed during exam"""

        tk.Label(card_frame, text=info_text,
                font=("Arial", 14),
                bg=self.colors["bg_secondary"],
                fg=self.colors["text_secondary"],
                justify="left").pack(pady=10)

        btn_frame = tk.Frame(card_frame, bg=self.colors["bg_secondary"])
        btn_frame.pack(pady=20)
        
        self.create_button(btn_frame, "Begin Exam", self.show_exam_guidelines, 
                          "success", 25).pack()

    def show_exam_guidelines(self):
        """Display exam guidelines"""
        self.clear_window()
        self.create_header("Exam Guidelines", "Please read carefully before proceeding")

        content_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        content_frame.pack(fill="both", expand=True, padx=60, pady=20)

        # Guidelines card
        guidelines_frame = tk.Frame(content_frame, bg=self.colors["bg_secondary"])
        guidelines_frame.pack(fill="both", expand=True, pady=20)

        guidelines_text = """📋 IMPORTANT EXAM RULES:

🔒 Security Measures:
   • Full screen mode will be activated
   • Window switching is disabled
   • All activity is monitored and recorded

👁️ Monitoring Requirements:
   • Keep your face visible to the camera at all times
   • Do not look away from the screen for extended periods
   • Maintain good lighting on your face

🚫 Prohibited Actions:
   • Opening other applications or browsers
   • Using external devices or materials
   • Communicating with others during the exam
   • Making excessive noise or movements

⚠️ Violation Consequences:
   • Suspicious activity will be flagged automatically
   • Multiple violations may result in exam termination
   • All activity logs will be included in your final report

By clicking "I Agree & Start", you acknowledge understanding and acceptance of these rules."""

        text_widget = tk.Text(guidelines_frame, 
                             font=("Arial", 11),
                             bg=self.colors["bg_secondary"],
                             fg=self.colors["text_primary"],
                             relief="flat", bd=0,
                             wrap="word", state="disabled",
                             height=20)
        text_widget.pack(fill="both", expand=True, padx=30, pady=30)
        
        text_widget.config(state="normal")
        text_widget.insert("1.0", guidelines_text)
        text_widget.config(state="disabled")

        # Agreement buttons
        btn_frame = tk.Frame(content_frame, bg=self.colors["bg_primary"])
        btn_frame.pack(pady=20)
        
        self.create_button(btn_frame, "I Agree & Start Exam", self.start_exam, 
                          "danger", 30).pack()

    def show_no_content(self):
        """Show when no slides or questions are available"""
        self.clear_window()
        self.create_header("ProctorY", "Content Not Found")

        content_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        content_frame.pack(fill="both", expand=True)

        message_frame = tk.Frame(content_frame, bg=self.colors["bg_secondary"])
        message_frame.pack(pady=100, padx=100, fill="both", expand=True)

        tk.Label(message_frame, text="📁 No Content Available",
                font=("Arial", 18, "bold"),
                bg=self.colors["bg_secondary"],
                fg=self.colors["warning"]).pack(pady=30)

        message_text = """No presentation slides found in 'slides' folder
No questions found in 'questions.json' file

Please ensure your content files are in the correct location:
• Slides: slides/slide1.png, slides/slide2.jpg, etc.
• Questions: questions.json"""

        tk.Label(message_frame, text=message_text,
                font=("Arial", 12),
                bg=self.colors["bg_secondary"],
                fg=self.colors["text_secondary"],
                justify="center").pack(pady=20)

    # ============================
    # EXAM MODE
    # ============================
    def start_exam(self):
        """Initialize exam mode with lockdown"""
        if not self.questions:
            messagebox.showerror("Error", "No questions available for exam!")
            return
            
        # Enable lockdown mode
        self.root.attributes("-fullscreen", True)
        self.root.protocol("WM_DELETE_WINDOW", self.disable_event)
        
        # Disable all possible hotkeys and key combinations
        hotkeys = [
            "<Alt_L><F4>", "<Alt_R><F4>",
            "<Control-Alt-Delete>", "<Control-Shift-Escape>",
            "<Escape>", "<Alt-Tab>", "<Alt-Shift-Tab>",
            "<Super_L>", "<Super_R>",  # Windows key
            "<Control-Alt-t>", "<Control-Alt-Tab>",
            "<Control-Shift-t>", "<Control-t>", "<Control-n>",
            "<Control-w>", "<Control-q>", "<Alt-F10>",
            "<F11>", "<F5>", "<Control-F5>", "<Control-r>",
            "<Control-l>", "<Control-d>", "<Control-h>",
            "<Control-j>", "<Control-k>", "<Control-Shift-i>",
            "<Control-Shift-j>", "<Control-u>", "<F12>",
            "<Control-Shift-n>", "<Control-Shift-p>",
            "<Alt-F4>", "<Control-Escape>", "<Win_L>", "<Win_R>"
        ]
        
        # Safely bind hotkeys with error handling
        for hotkey in hotkeys:
            try:
                self.root.bind_all(hotkey, self.disable_hotkey)
            except tk.TclError:
                pass  # Skip invalid key combinations
        
        # Bind key press events for additional security
        self.root.bind("<KeyPress>", self.check_forbidden_keys)
        self.root.focus_set()  # Ensure window has focus

        # Reset exam state
        self.current_q = 0
        self.answers = {}
        self.time_remaining = self.exam_duration
        
        # Create exam layout and start timer
        self.create_exam_layout()
        self.start_timer()
        self.show_question()

    def show_question(self):
        """Display current question in exam mode"""
        # Clear main frame only
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        if self.current_q < len(self.questions):
            q = self.questions[self.current_q]

            # Question header
            header_frame = tk.Frame(self.main_frame, bg=self.colors["bg_primary"])
            header_frame.pack(fill="x", padx=30, pady=20)
            
            progress_text = f"Question {self.current_q + 1} of {len(self.questions)}"
            tk.Label(header_frame, text=progress_text,
                    font=("Arial", 14),
                    bg=self.colors["bg_primary"],
                    fg=self.colors["text_secondary"]).pack(anchor="w")

            # Progress bar
            progress = (self.current_q / len(self.questions)) * 100
            progress_frame = tk.Frame(header_frame, bg=self.colors["bg_primary"])
            progress_frame.pack(fill="x", pady=(10, 0))
            
            progress_bg = tk.Frame(progress_frame, bg=self.colors["bg_secondary"], height=4)
            progress_bg.pack(fill="x")
            
            progress_fill = tk.Frame(progress_bg, bg=self.colors["accent"], height=4)
            progress_fill.place(relwidth=progress/100, relheight=1)

            # Question content
            question_frame = tk.Frame(self.main_frame, bg=self.colors["bg_secondary"])
            question_frame.pack(fill="both", expand=True, padx=30, pady=(20, 30))

            # Question text
            q_label = tk.Label(question_frame, text=q["question"],
                              font=("Arial", 16, "bold"),
                              bg=self.colors["bg_secondary"],
                              fg=self.colors["text_primary"],
                              wraplength=600, justify="left")
            q_label.pack(pady=30, padx=30, anchor="w")

            # Options
            self.var = tk.StringVar(value="")
            options_frame = tk.Frame(question_frame, bg=self.colors["bg_secondary"])
            options_frame.pack(fill="x", padx=50, pady=20)

            for i, opt in enumerate(q["options"]):
                opt_frame = tk.Frame(options_frame, bg=self.colors["bg_primary"], 
                                   relief="flat", bd=1)
                opt_frame.pack(fill="x", pady=5)
                
                rb = tk.Radiobutton(opt_frame, text=f"  {chr(65+i)}. {opt}",
                                   variable=self.var, value=opt,
                                   font=("Arial", 12),
                                   bg=self.colors["bg_primary"],
                                   fg=self.colors["text_primary"],
                                   selectcolor=self.colors["accent"],
                                   activebackground=self.colors["bg_primary"],
                                   relief="flat", bd=0)
                rb.pack(anchor="w", padx=20, pady=10)

    def show_question(self):
        """Display current question in exam mode"""
        # Clear main frame only
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        if self.current_q < len(self.questions):
            q = self.questions[self.current_q]

            # Question header with navigation
            header_frame = tk.Frame(self.main_frame, bg=self.colors["bg_primary"])
            header_frame.pack(fill="x", padx=30, pady=20)
            
            # Progress and question info
            info_frame = tk.Frame(header_frame, bg=self.colors["bg_primary"])
            info_frame.pack(fill="x")
            
            progress_text = f"Question {self.current_q + 1} of {len(self.questions)}"
            tk.Label(info_frame, text=progress_text,
                    font=("Arial", 14),
                    bg=self.colors["bg_primary"],
                    fg=self.colors["text_secondary"]).pack(side="left")
            
            # Bookmark indicator
            bookmark_text = "🔖" if self.current_q in self.bookmarked_questions else "☆"
            tk.Label(info_frame, text=bookmark_text,
                    font=("Arial", 16),
                    bg=self.colors["bg_primary"],
                    fg=self.colors["warning"]).pack(side="right")

            # Progress bar
            progress = (self.current_q / len(self.questions)) * 100
            progress_frame = tk.Frame(header_frame, bg=self.colors["bg_primary"])
            progress_frame.pack(fill="x", pady=(10, 0))
            
            progress_bg = tk.Frame(progress_frame, bg=self.colors["bg_secondary"], height=4)
            progress_bg.pack(fill="x")
            
            progress_fill = tk.Frame(progress_bg, bg=self.colors["accent"], height=4)
            progress_fill.place(relwidth=progress/100, relheight=1)

            # Question content
            question_frame = tk.Frame(self.main_frame, bg=self.colors["bg_secondary"])
            question_frame.pack(fill="both", expand=True, padx=30, pady=(20, 0))

            # Question text
            q_label = tk.Label(question_frame, text=q["question"],
                              font=("Arial", 16, "bold"),
                              bg=self.colors["bg_secondary"],
                              fg=self.colors["text_primary"],
                              wraplength=600, justify="left")
            q_label.pack(pady=30, padx=30, anchor="w")

            # Options
            self.var = tk.StringVar(value=self.answers.get(self.current_q, ""))
            options_frame = tk.Frame(question_frame, bg=self.colors["bg_secondary"])
            options_frame.pack(fill="x", padx=50, pady=20)

            for i, opt in enumerate(q["options"]):
                opt_frame = tk.Frame(options_frame, bg=self.colors["bg_primary"], 
                                   relief="flat", bd=1)
                opt_frame.pack(fill="x", pady=5)
                
                rb = tk.Radiobutton(opt_frame, text=f"  {chr(65+i)}. {opt}",
                                   variable=self.var, value=opt,
                                   font=("Arial", 12),
                                   bg=self.colors["bg_primary"],
                                   fg=self.colors["text_primary"],
                                   selectcolor=self.colors["accent"],
                                   activebackground=self.colors["bg_primary"],
                                   relief="flat", bd=0)
                rb.pack(anchor="w", padx=20, pady=10)

            # Bottom navigation panel
            nav_frame = tk.Frame(self.main_frame, bg=self.colors["bg_primary"], height=80)
            nav_frame.pack(fill="x", padx=30, pady=10)
            nav_frame.pack_propagate(False)
            
            # Left side navigation buttons
            left_nav = tk.Frame(nav_frame, bg=self.colors["bg_primary"])
            left_nav.pack(side="left", fill="y")
            
            # Previous button
            if self.current_q > 0:
                prev_btn = self.create_button(left_nav, "← Previous", self.prev_question, "warning", 12)
                prev_btn.pack(side="left", padx=(0, 10))
            
            # Bookmark button
            bookmark_text = "🔖 Unbookmark" if self.current_q in self.bookmarked_questions else "☆ Bookmark"
            bookmark_btn = self.create_button(left_nav, bookmark_text, self.toggle_bookmark, "warning", 12)
            bookmark_btn.pack(side="left", padx=5)
            
            # Right side navigation
            right_nav = tk.Frame(nav_frame, bg=self.colors["bg_primary"])
            right_nav.pack(side="right", fill="y")
            
            # Question overview button
            overview_btn = self.create_button(right_nav, "📋 Overview", self.show_question_overview, "primary", 12)
            overview_btn.pack(side="right", padx=(10, 0))
            
            # Next/Submit button
            next_text = "Submit Exam" if self.current_q == len(self.questions) - 1 else "Next →"
            next_style = "success" if self.current_q == len(self.questions) - 1 else "primary"
            next_btn = self.create_button(right_nav, next_text, self.next_question, next_style, 12)
            next_btn.pack(side="right", padx=5)

        else:
            self.submit_exam()

    def next_question(self):
        """Move to next question"""
        # Save current answer if provided
        if hasattr(self, 'var') and self.var.get():
            self.answers[self.current_q] = self.var.get()
        
        if self.current_q < len(self.questions) - 1:
            self.current_q += 1
            self.show_question()
        else:
            # Last question - submit exam
            if hasattr(self, 'var') and not self.var.get():
                result = messagebox.askyesno("Submit Exam", 
                                           "Current question is not answered. Submit anyway?")
                if not result:
                    return
            self.submit_exam()

    def prev_question(self):
        """Move to previous question"""
        # Save current answer
        if hasattr(self, 'var') and self.var.get():
            self.answers[self.current_q] = self.var.get()
        
        if self.current_q > 0:
            self.current_q -= 1
            self.show_question()

    def toggle_bookmark(self):
        """Toggle bookmark for current question"""
        if self.current_q in self.bookmarked_questions:
            self.bookmarked_questions.remove(self.current_q)
        else:
            self.bookmarked_questions.add(self.current_q)
        self.show_question()  # Refresh to update bookmark display

    def show_question_overview(self):
        """Show question overview window"""
        overview_window = tk.Toplevel(self.root)
        overview_window.title("Question Overview")
        overview_window.geometry("400x500")
        overview_window.configure(bg=self.colors["bg_primary"])
        overview_window.attributes("-topmost", True)
        
        # Header
        tk.Label(overview_window, text="📋 Question Overview",
                font=("Arial", 16, "bold"),
                bg=self.colors["bg_primary"],
                fg=self.colors["text_primary"]).pack(pady=10)
        
        # Scrollable question list
        canvas = tk.Canvas(overview_window, bg=self.colors["bg_primary"])
        scrollbar = ttk.Scrollbar(overview_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors["bg_primary"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Question items
        for i in range(len(self.questions)):
            item_frame = tk.Frame(scrollable_frame, bg=self.colors["bg_secondary"], relief="flat", bd=1)
            item_frame.pack(fill="x", padx=10, pady=2)
            
            # Status indicators
            answered = "✓" if i in self.answers and self.answers[i] else "○"
            bookmarked = "🔖" if i in self.bookmarked_questions else ""
            current = "→" if i == self.current_q else ""
            
            status_text = f"{current} Q{i+1} {answered} {bookmarked}"
            
            btn = tk.Button(item_frame, text=status_text,
                           font=("Arial", 10),
                           bg=self.colors["bg_secondary"],
                           fg=self.colors["text_primary"],
                           relief="flat", bd=0,
                           anchor="w",
                           command=lambda x=i: self.jump_to_question(x, overview_window))
            btn.pack(fill="x", padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        tk.Button(overview_window, text="Close",
                 bg=self.colors["accent"], fg="white",
                 command=overview_window.destroy).pack(pady=10)

    def jump_to_question(self, question_num, window):
        """Jump to specific question"""
        # Save current answer
        if hasattr(self, 'var') and self.var.get():
            self.answers[self.current_q] = self.var.get()
        
        self.current_q = question_num
        window.destroy()
        self.show_question()

    # ============================
    # MONITORING CONTROLS
    # ============================
    def toggle_monitoring(self, monitor_type):
        """Toggle monitoring display for different types"""
        if monitor_type in self.monitoring_windows:
            self.close_monitoring()
        else:
            self.show_monitoring(monitor_type)

    def show_monitoring(self, monitor_type):
        """Display monitoring output"""
        # Close any existing monitoring window
        self.close_monitoring()
        
        # Show monitoring output area
        self.monitoring_output.pack(fill="x", pady=(5, 0))
        
        # Clear previous content
        self.monitoring_text.delete(1.0, tk.END)
        
        # Simulate monitoring data based on type
        monitor_data = {
            "devices": """🔌 Connected Devices Monitor:
• USB Mouse: Logitech M705 - ALLOWED
• USB Keyboard: Dell KB216 - ALLOWED  
• Webcam: HD Pro C920 - ACTIVE
• Bluetooth: No devices detected
• External Storage: None detected
• Network Adapters: WiFi Active

⚠️ Note: Connect your device detection script here""",
            
            "network": """🌐 Network Activity Monitor:
• Status: Connected (192.168.1.105)
• Bandwidth: 25.4 Mbps Down / 5.2 Mbps Up
• Active Connections: 3
• Blocked Attempts: 0
• DNS Queries: Normal
• Packet Analysis: Clean

🔍 Real-time monitoring active...
Connect your network monitoring script here""",
            
            "noise": """🎤 Background Noise Analysis:
• Ambient Level: 42 dB (Normal)
• Voice Detection: None
• Background Music: None detected
• Sudden Sounds: 0 in last 5 min
• Audio Quality: Clear
• Microphone Status: Active

📊 Noise threshold: <60dB
Connect your audio monitoring script here""",
            
            "failures": """⚠️ System Failure Monitor:
• Network Disconnections: 0
• Camera Failures: 0
• System Crashes: 0
• Unauthorized Access: 0
• Window Focus Lost: 0
• Process Terminations: 0

✅ All systems operating normally
Connect your failure detection script here"""
        }
        
        self.monitoring_text.insert(tk.END, monitor_data.get(monitor_type, "No data available"))
        self.monitoring_windows[monitor_type] = True

    def close_monitoring(self):
        """Close monitoring output"""
        self.monitoring_output.pack_forget()
        self.monitoring_windows.clear()

    # ============================
    # ENHANCED SECURITY
    # ============================
    def check_forbidden_keys(self, event):
        """Check for forbidden key combinations and individual keys"""
        # Block function keys
        forbidden_keys = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12']
        
        # Block Windows key and system keys
        system_keys = ['Super_L', 'Super_R', 'Win_L', 'Win_R', 'Meta_L', 'Meta_R', 'Hyper_L', 'Hyper_R']
        
        # Check for forbidden individual keys
        if event.keysym in forbidden_keys or event.keysym in system_keys:
            return "break"
        
        # Check for dangerous key combinations
        state = event.state
        
        # Alt+Tab (state 8 = Alt)
        if state & 0x8 and event.keysym == 'Tab':
            return "break"
            
        # Ctrl+Shift+Esc (state 4 = Ctrl, state 1 = Shift)
        if (state & 0x4) and (state & 0x1) and event.keysym == 'Escape':
            return "break"
            
        # Ctrl+Alt combinations
        if (state & 0x4) and (state & 0x8):  # Ctrl+Alt
            return "break"
        
        # Block Windows key combinations (state varies by system)
        if event.keysym in ['Tab', 'r', 'l', 'd', 'e', 'i', 'x', 's'] and (state & 0x40000):
            return "break"
    def submit_exam(self):
        """Submit exam and show results"""
        self.timer_running = False
        
        # Exit lockdown mode
        self.root.attributes("-fullscreen", False)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        
        # Calculate score
        score = 0
        for i, q in enumerate(self.questions):
            if self.answers.get(i) == q.get("answer"):
                score += 1

        # Generate report
        percentage = (score / len(self.questions)) * 100 if self.questions else 0
        time_taken = self.exam_duration - self.time_remaining
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "score": score,
            "total_questions": len(self.questions),
            "percentage": round(percentage, 1),
            "time_taken_minutes": round(time_taken / 60, 1),
            "time_remaining_minutes": round(self.time_remaining / 60, 1),
            "status": self.get_status(percentage),
            "monitoring_flags": [
                "Face detection: Active",
                "Network monitoring: Stable", 
                "Window focus: Maintained",
                "Suspicious activity: None detected"
            ]
        }

        # Save report
        try:
            with open("exam_report.json", "w") as f:
                json.dump(report, f, indent=4)
        except Exception as e:
            print(f"Error saving report: {e}")

        self.show_report(report)

    def get_status(self, percentage):
        """Get exam status based on percentage"""
        if percentage >= 80:
            return "Excellent"
        elif percentage >= 70:
            return "Good"
        elif percentage >= 60:
            return "Satisfactory"
        else:
            return "Needs Improvement"

    def show_report(self, report):
        """Display exam results"""
        self.clear_window()
        self.create_header("Exam Completed", "Your results are ready")

        content_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        content_frame.pack(fill="both", expand=True, padx=60, pady=40)

        # Results card
        results_frame = tk.Frame(content_frame, bg=self.colors["bg_secondary"])
        results_frame.pack(fill="both", expand=True)

        # Score display
        score_frame = tk.Frame(results_frame, bg=self.colors["bg_secondary"])
        score_frame.pack(pady=30)

        score_text = f"{report['score']}/{report['total_questions']}"
        tk.Label(score_frame, text=score_text,
                font=("Arial", 36, "bold"),
                bg=self.colors["bg_secondary"],
                fg=self.colors["success"]).pack()

        tk.Label(score_frame, text=f"{report['percentage']}% • {report['status']}",
                font=("Arial", 18),
                bg=self.colors["bg_secondary"],
                fg=self.colors["text_secondary"]).pack()

        # Details
        details_frame = tk.Frame(results_frame, bg=self.colors["bg_secondary"])
        details_frame.pack(pady=20, padx=40, fill="x")

        details = [
            ("Time Taken", f"{report['time_taken_minutes']} minutes"),
            ("Time Remaining", f"{report['time_remaining_minutes']} minutes"),
            ("Completion", f"{report['timestamp']}")
        ]

        for label, value in details:
            row = tk.Frame(details_frame, bg=self.colors["bg_secondary"])
            row.pack(fill="x", pady=5)
            
            tk.Label(row, text=f"{label}:",
                    font=("Arial", 12, "bold"),
                    bg=self.colors["bg_secondary"],
                    fg=self.colors["text_secondary"]).pack(side="left")
            
            tk.Label(row, text=value,
                    font=("Arial", 12),
                    bg=self.colors["bg_secondary"],
                    fg=self.colors["text_primary"]).pack(side="right")

        # Monitoring summary
        monitoring_frame = tk.Frame(results_frame, bg=self.colors["bg_primary"])
        monitoring_frame.pack(fill="x", padx=40, pady=20)

        tk.Label(monitoring_frame, text="📊 Monitoring Summary",
                font=("Arial", 14, "bold"),
                bg=self.colors["bg_primary"],
                fg=self.colors["text_primary"]).pack(pady=(0, 10))

        for flag in report["monitoring_flags"]:
            tk.Label(monitoring_frame, text=f"✓ {flag}",
                    font=("Arial", 10),
                    bg=self.colors["bg_primary"],
                    fg=self.colors["success"]).pack(anchor="w")

        # Exit button
        btn_frame = tk.Frame(results_frame, bg=self.colors["bg_secondary"])
        btn_frame.pack(pady=30)
        
        self.create_button(btn_frame, "Exit Application", self.root.destroy, 
                          "primary", 20).pack()

    # ============================
    # UTILITY METHODS
    # ============================
    def clear_window(self):
        """Clear all widgets from root window"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def disable_event(self):
        """Disable window close during exam"""
        messagebox.showwarning("Exam In Progress", 
                              "Cannot exit during exam. Please complete all questions.")

    def disable_hotkey(self, event=None):
        """Disable keyboard shortcuts during exam"""
        return "break"


if __name__ == "__main__":
    root = tk.Tk()
    
    # Set window icon if available
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    # Additional security measures
    try:
        # Try to disable task manager and other system shortcuts
        import ctypes
        ctypes.windll.user32.RegisterHotKeyW(None, 1, 0x0002 | 0x0004, 0x73)  # Ctrl+Alt+Del
        ctypes.windll.user32.RegisterHotKeyW(None, 2, 0x0002, 0x1B)  # Ctrl+Esc
    except:
        pass  # Not on Windows or insufficient permissions
    
    app = ProctorYApp(root)
    root.mainloop()