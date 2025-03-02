from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
from ultralytics import YOLO
import threading
import torch
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Global variables
camera = None
streaming = False
model = YOLO("yolov8n.pt")  # Load YOLOv8 model
alert_triggered = False  # To ensure beep or email triggers only once per detection

# Email credentials
sender_email = "authoritywildlife@gmail.com"  # Replace with your email
sender_password = "kugc pjcc mvlo wawm"  # Replace with your email password
recipient_email = "karanamakshay05@gmail.com"  # Replace with the target email

# Function to send an email
def send_email_alert():
    subject = "Animal Detection Alert"
    body = "An animal has been detected in your farm. Please check immediately."
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)  # Use Gmail's SMTP server
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)  # Login to the email account
        server.sendmail(sender_email, recipient_email, msg.as_string())  # Send the email
        server.quit()
        print("Email alert sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Frame generation for streaming
def generate_frames():
    global camera, streaming, alert_triggered

    if camera is None:
        camera = cv2.VideoCapture(0)  # Open the default camera

    if not camera.isOpened():
        print("Error: Camera not accessible.")
        return

    while streaming:
        try:
            success, frame = camera.read()
            if not success:
                print("Error: Failed to capture frame.")
                break

            # Convert frame to RGB (YOLO expects RGB format)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Resize frame for YOLO input (assuming 640x640 input size)
            frame_resized = cv2.resize(frame_rgb, (640, 640))

            # Normalize frame values to [0, 1]
            frame_normalized = frame_resized / 255.0

            # Convert the frame to a tensor (compatible with YOLO)
            frame_tensor = torch.tensor(frame_normalized).float()
            frame_tensor = frame_tensor.permute(2, 0, 1).unsqueeze(0)  # Shape: (1, C, H, W)

            # Use model's predict method
            results = model(frame_tensor)  # Process frame using YOLOv8
            detections = results[0].boxes.data  # Get the tensor of detections

            animal_detected = False  # Flag to track animal detection for alert triggering

            # Process each detection in the frame
            for detection in detections:
                detection = detection.cpu().numpy()  # Convert detection to NumPy array
                x1, y1, x2, y2, confidence, class_id = detection[:6]

                class_id = int(class_id)  # Convert class_id to int

                # Class IDs for humans and animals (adjust based on YOLOv8's COCO labels)
                if class_id in [1, 16, 17, 18]:  # 1=person, 16=bird, 17=cat, 18=dog
                    label = "Animal" if class_id in [16, 17, 18] else "Human"
                    color = (0, 255, 0) if label == "Animal" else (255, 0, 0)  # Green for animals, Blue for humans

                    # Draw bounding box and label on the frame
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(
                        frame,
                        f"{label} {confidence:.2f}",
                        (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        color,
                        2
                    )

                    # Trigger alert and display message if an animal is detected
                    if label == "Animal" and not alert_triggered:
                        alert_triggered = True
                        animal_detected = True
                        
                        # Send email alert in a separate thread
                        threading.Thread(target=send_email_alert).start()

                        # Display alert message on the frame
                        cv2.putText(
                            frame,
                            "ALERT: Animal Detected!",
                            (50, 50),  # Display at the top-left corner
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.2,
                            (0, 0, 255),  # Red color for alert message
                            3
                        )

            # Reset alert trigger if no animals are detected
            if not animal_detected:
                alert_triggered = False

            # Encode the frame for video streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame in the required format for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        except Exception as e:
            print(f"Error in generate_frames: {e}")
            break

    # Release the camera when streaming stops
    if camera:
        camera.release()
        camera = None

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    global streaming
    if not streaming:
        streaming = True
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global streaming
    streaming = False
    return jsonify({"status": "stopped"})


if __name__ == "__main__":
    app.run(debug=True)
