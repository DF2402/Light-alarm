import "./IotCard.css";
import { useEffect, useState } from "react";
import { API_URL } from "../config";

const IotCard = () => {
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  const getLastMessage = async () => {
    try {
      const response = await fetch(`${API_URL}/api/get-last-message`);
      if (response.ok) {
        const data = await response.json();
        setLastMessage(data.message);
      } else {
        throw new Error("Failed to get last message");
      }
    } catch (error) {
      console.error("Error:", error);
      setLastMessage("Failed to connect to server");
    }
  };

  useEffect(() => {
    getLastMessage();
    const interval = setInterval(() => {
      getLastMessage();
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="iot-card">
      <div className="iot-card-header">
        <h2>IoT</h2>
      </div>
      <div className="iot-card-body">
        <div className="iot-card-body-content">
          <p>{lastMessage ? lastMessage : "No message received"}</p>
        </div>
      </div>
    </div>
  );
};

export default IotCard;
