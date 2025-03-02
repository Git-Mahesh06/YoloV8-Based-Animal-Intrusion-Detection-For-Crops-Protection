document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start-detection');
    const videoContainer = document.getElementById('video-container');
    const videoStream = document.getElementById('video-stream');
    const alertBox = document.createElement('div'); // Alert box for dynamic messages

    // Add the alert box to the DOM
    alertBox.id = 'alert-box';
    alertBox.style.display = 'none';
    alertBox.style.position = 'absolute';
    alertBox.style.top = '10px';
    alertBox.style.left = '50%';
    alertBox.style.transform = 'translateX(-50%)';
    alertBox.style.padding = '10px 20px';
    alertBox.style.backgroundColor = 'rgba(10, 8, 8, 0.8)';
    alertBox.style.color = '#fff';
    alertBox.style.borderRadius = '5px';
    alertBox.style.zIndex = '1000';
    document.body.appendChild(alertBox);

    // Function to show alert messages
    function showAlert(message, timeout = 3000) {
        alertBox.textContent = message;
        alertBox.style.display = 'block';
        setTimeout(() => {
            alertBox.style.display = 'none';
        }, timeout);
    }

    // Start video stream on button click
    startButton.addEventListener('click', () => {
        videoContainer.style.display = 'block';
        videoStream.src = '/video_feed';
        startButton.textContent = 'Detection in Progress...';
        startButton.style.background = '#28a745';
        startButton.style.boxShadow = '0 4px 10px rgba(40, 167, 69, 0.5)';
        startButton.disabled = true;

        // Display starting message
        showAlert('Detection started. Press "Q" to stop.');
    });

    // Listen for key press event to stop video stream
    document.addEventListener('keydown', (event) => {
        if (event.key.toLowerCase() === 'q') {
            // Stop the video stream
            fetch('/stop_stream', { method: 'POST' })
                .then((response) => response.json())
                .then((data) => {
                    if (data.status === 'stopped') {
                        videoStream.src = ''; // Clear the video source
                        videoContainer.style.display = 'none'; // Hide the video container

                        // Reset button state
                        startButton.textContent = 'Start Detection';
                        startButton.style.background = '#007BFF';
                        startButton.style.boxShadow = '0 4px 10px rgba(0, 123, 255, 0.3)';
                        startButton.disabled = false;

                        // Display stopping message
                        showAlert('Video stream stopped, and camera released!');
                    }
                })
                .catch((error) => {
                    console.error('Error stopping the stream:', error);
                    showAlert('Error stopping the video stream.', 5000);
                });
        }
    });
});
