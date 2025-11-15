import "./IotCard.css";
import { useEffect, useState } from "react";
import { API_URL } from "../config";

const IotCard = () => {
  const [sensorData, setSensorData] = useState<string | null>(null);
  const [deviceList, setDeviceList] = useState<string[]>([]);


  const getDeviceList = async () => {
    try {
      const response = await fetch(`${API_URL}/api/devices`);
      if (response.ok) {
        const data = await response.json();
        setDeviceList(data.devices);
      }
    } catch (error) {
      console.error("Error:", error);
      setDeviceList([]);
    }
  };  

  const toggleLight = async (device: string) => {
    try {
      const response = await fetch(`${API_URL}/api/send_toggle/${device}`);
      if (response.ok) {
        const data = await response.json();
        console.log(data);
      } else {
        throw new Error("Failed to toggle light");
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };

  useEffect(() => {
    getDeviceList();
    const interval = setInterval(() => {
      getDeviceList();
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="iot-card">
      <div className="iot-card-header">
        <h2>Device List</h2>
      </div>
      <div className="iot-card-body">
        <div className="iot-card-body-content">
          {deviceList.map((device) => (
            <div key={device} className="device-item">
              {device}
              <button className="btn" onClick={() => toggleLight(device)}>Toggle Light</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default IotCard;
