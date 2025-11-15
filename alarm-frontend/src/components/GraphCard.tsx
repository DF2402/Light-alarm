import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import { API_URL } from "../config";
import "./GraphCard.css";

interface GraphCardProps {
    deviceId: string;
}

const GraphCard = ({ deviceId }: GraphCardProps) => {

    const [temperatureData, setTemperatureData] = useState<any[]>([]);
    const [humidityData, setHumidityData] = useState<any[]>([]);


    const getTemperatureData = async () => {
        const response = await fetch(`${API_URL}/api/sensor-history/${deviceId}?sensor_id=temperature&hours=1`);
        if (response.ok) {
            const data = await response.json();
            setTemperatureData(data.data);
        } else {
            throw new Error("Failed to get temperature data");
        }
    };

    const getHumidityData = async () => {
        const response = await fetch(`${API_URL}/api/sensor-history/${deviceId}?sensor_id=humidity&hours=1`);
        if (response.ok) {
            const data = await response.json();
            setHumidityData(data.data);
        } else {
            throw new Error("Failed to get humidity data");
        }
    };

    useEffect(() => {
        getTemperatureData();
        getHumidityData();
        const interval = setInterval(() => {
            getTemperatureData();
            getHumidityData();
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="graph-card">
            <div className="graph-card-header">
                <h2>Temperature and Humidity Graph</h2>
            </div>
            <div className="graph-card-body">
                <div className="graph-card-body-content">
                    <LineChart data={temperatureData}>
                        <XAxis dataKey="timestamp" />
                        <YAxis />
                        <CartesianGrid stroke="#ccc" strokeDasharray="5 5" />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="value" stroke="#8884d8" />
                    </LineChart>
                    <LineChart data={humidityData}>
                        <XAxis dataKey="timestamp" />
                        <YAxis />
                        <CartesianGrid stroke="#ccc" strokeDasharray="5 5" />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="value" stroke="#8884d8" />
                    </LineChart>
                </div>
            </div>
        </div>
    );
};

export default GraphCard;