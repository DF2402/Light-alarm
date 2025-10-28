import { useState } from "react";
import { API_URL } from "../config";
import "./CameraCard.css";

const CameraCard = () => {
    const [image, setImage] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [message, setMessage] = useState<string | null>(null);
    
    const takeImage = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/take-image`);
            if (response.ok) {
                const data = await response.json();
                setImage(data.image.toString('base64'));
                setMessage(data.message);
            } else {
                setMessage("Failed to take image");
            }
        } catch (error) {
            console.error('Error:', error);
            setMessage("Failed to connect to server");
        }
        setLoading(false);
    }

    return (
        <div className="camera-card">
            <div className="camera-card-header">
                <h2>🎥 攝像頭</h2>
            </div>
            <div className="camera-card-body">
                
                <div className="image-container">
                    {image && <img src={`data:image/jpeg;base64,${image}`} alt="Taken Image" />}
                </div>
                <div className="message-container">
                    {loading && <p>Loading...</p>}
                    {message && <p className="message">{message}</p>}
                </div>
                
            </div>
            <button className="side-btn" onClick={takeImage}>{loading ? 'Taking...' : 'Take Image'}</button>
        </div>
    )
}

export default CameraCard;