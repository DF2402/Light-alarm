import { useState, useEffect } from "react";
import "./ClockCard.css";
import { API_URL } from "../config";

const ClockCard = () => {
    
    const [currentTime, setCurrentTime] = useState(new Date());
    const [currentClock, setCurrentClock] = useState<string | null>(null);
    useEffect(() => {

        const timer = setInterval(() => {
            setCurrentTime(new Date());
            getCurrentClock();
        }, 1000); 

        return () => {
            clearInterval(timer);
        };
    }, []); 

    const getCurrentClock = async () => {
        
        try {
            const response = await fetch(`${API_URL}/api/timer-time`);
            const data = await response.json();
            if (response.ok) {
                setCurrentClock(data.timer_time);
            } else {
                setCurrentClock("Failed to get timer time");
            }
        } catch (error) {
            console.error('Error:', error);
            setCurrentClock("Failed to connect to server");
        }
    };

    return (
        <div className="clock-card">
            <div className="clock-card-header">
                <h2>⏰ 當前時間</h2>
            </div>
            <div className="clock-card-body">
                <div className="clock-card-body-content">
                    <p>{currentTime.toLocaleString()}</p>
                </div>
            </div>

            <div className="clock-card-header">
                <h2>⏰ 鬧鐘設置時間</h2>
            </div>
            <div className="clock-card-body-content">
                <p>{currentClock}</p>
            </div>
        </div>
    );
};

export default ClockCard;