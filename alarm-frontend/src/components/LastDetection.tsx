import { useState, useEffect } from "react";
import { API_URL } from "../config";
import "./LastDetection.css";

const LastDetection = () => {
    const [detectionResult, setDetectionResult] = useState<string | null>(null);
    const [detectionTime, setDetectionTime] = useState<string | null>(null);
    const [image, setImage] = useState<string | null>(null);
    const getLastDetection = async () => {
        try {
            const response = await fetch(`${API_URL}/api/last-detection`);
            if (response.ok) {
                const data = await response.json();
                console.log(data);
                if (data.status === 'success') {
                    setDetectionResult(data.detection_result);
                    setDetectionTime(data.detection_time);
                    setImage(data.image);
                } else {
                    setDetectionResult(null);
                    setDetectionTime(null);
                    setImage(null);
                    throw new Error(data.message);
                }
            } else {
                throw new Error("Failed to get last detection");
            }
        } catch (error) {
            console.error("Error:", error);
        }
    };
    useEffect(() => {
        getLastDetection();
        const interval = setInterval(() => {
            getLastDetection();
        }, 1000);
        return () => clearInterval(interval);
    }, []);
    return (
        <div className="last-detection">
            <div className="last-detection-header">
                <h2>Last Detection</h2>
            </div>
            <div className="last-detection-body">
                <p>Detection Result: {detectionResult ? detectionResult : "No detection result"}</p>
                <p>Detection Time: {detectionTime ? detectionTime : "No detection time"}</p>
                {image && <img src={`data:image/jpeg;base64,${image}`} alt="Last Detection" />}
            </div>
        </div>
    );
};

export default LastDetection;