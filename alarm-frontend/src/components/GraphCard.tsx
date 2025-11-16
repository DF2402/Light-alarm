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
        try {
            const response = await fetch(`${API_URL}/api/sensor-history/${deviceId}?sensor_id=temperature&hours=24`);
            if (response.ok) {
                const data = await response.json();
                console.log('Temperature hourly data:', data);
                setTemperatureData(data.data || []);
            } else {
                console.error("Failed to get temperature data");
            }
        } catch (err) {
            console.error("Error fetching temperature data:", err);
        }
    };

    const getHumidityData = async () => {
        try {
            const response = await fetch(`${API_URL}/api/sensor-history/${deviceId}?sensor_id=humidity&hours=24`);
            if (response.ok) {
                const data = await response.json();
                console.log('Humidity hourly data:', data);
                setHumidityData(data.data || []);
            } else {
                console.error("Failed to get humidity data");
            }
        } catch (err) {
            console.error("Error fetching humidity data:", err);
        }
    };

    useEffect(() => {
        getTemperatureData();
        getHumidityData();
        const interval = setInterval(() => {
            getTemperatureData();
            getHumidityData();
        }, 60000);
        return () => clearInterval(interval);
    }, []);

    const formatTimestamp = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleString('zh-TW', { 
            month: '2-digit', 
            day: '2-digit', 
            hour: '2-digit',
            hour12: false
        });
    };

    return (
        <div className="graph-card">
            <div className="graph-card-header">
                <h2>Temperature and Humidity Graph (Hourly Average)</h2>
            </div>
            <div className="graph-card-body">
                <div className="graph-card-body-content">
                    <div style={{ marginBottom: '30px' }}>
                        <h3 style={{ marginBottom: '10px', color: '#333' }}>Temperature (°C)</h3>
                        {temperatureData.length > 0 ? (
                            <LineChart width={500} height={250} data={temperatureData}>
                                <XAxis 
                                    dataKey="timestamp" 
                                    tickFormatter={formatTimestamp}
                                    angle={-45}
                                    textAnchor="end"
                                    height={70}
                                />
                                <YAxis />
                                <CartesianGrid stroke="#ccc" strokeDasharray="5 5" />
                                <Tooltip 
                                    labelFormatter={formatTimestamp}
                                    formatter={(value: number) => [`${value}°C`, 'Temperature']}
                                />
                                <Legend />
                                <Line type="monotone" dataKey="value" stroke="#ff6b6b" strokeWidth={2} name="Temperature" />
                            </LineChart>
                        ) : (
                            <p style={{ textAlign: 'center', color: '#999' }}>No data available</p>
                        )}
                    </div>
                    <div>
                        <h3 style={{ marginBottom: '10px', color: '#333' }}>Humidity (%)</h3>
                        {humidityData.length > 0 ? (
                            <LineChart width={500} height={250} data={humidityData}>
                                <XAxis 
                                    dataKey="timestamp" 
                                    tickFormatter={formatTimestamp}
                                    angle={-45}
                                    textAnchor="end"
                                    height={70}
                                />
                                <YAxis />
                                <CartesianGrid stroke="#ccc" strokeDasharray="5 5" />
                                <Tooltip 
                                    labelFormatter={formatTimestamp}
                                    formatter={(value: number) => [`${value}%`, 'Humidity']}
                                />
                                <Legend />
                                <Line type="monotone" dataKey="value" stroke="#4ecdc4" strokeWidth={2} name="Humidity" />
                            </LineChart>
                        ) : (
                            <p style={{ textAlign: 'center', color: '#999' }}>No data available</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GraphCard;