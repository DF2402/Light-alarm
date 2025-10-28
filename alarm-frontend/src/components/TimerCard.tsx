import { useState } from "react";
import "./TimerCard.css";
import { API_URL } from "../config";

interface TimerCardProps {
    onTimerSet?: (time: string) => void;
}


const TimerCard = ({ onTimerSet }: TimerCardProps) => {
    const [hours, setHours] = useState<number>(0);
    const [minutes, setMinutes] = useState<number>(0);
   
    const[loading, setLoading] = useState<boolean>(false);
    const[message, setMessage] = useState<string>("");

    const increment = (setter:React.Dispatch<React.SetStateAction<number>>,max: number,current: number) => {
        setter(current + 1 > max ? 0 : current + 1);
    };
    const decrement = (setter: React.Dispatch<React.SetStateAction<number>>,max: number,current: number) => {
        setter(current - 1 < 0 ? max : current - 1);
    };

    const handleInputChange = (
        setter: React.Dispatch<React.SetStateAction<number>>,
        max: number,
        rawValue: string
      ) => {
        let value = rawValue.replace(/[^0-9]/g, '');
        if (value.length > 2) {
          value = value.slice(-2);
        }
        let num = parseInt(value.replace(/^0+(?=\d)/, ''), 10);
        if (isNaN(num)) num = 0;
        if (num > max) num = max;
        if (num < 0) num = 0;
        setter(num);
      };

    const handleSubmit = async () => {
    const time = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    setLoading(true);
    setMessage("");

    try {
        const response = await fetch(`${API_URL}/api/set-timer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ time }),
        });
        if (response.ok) {
            const data = await response.json();
            setMessage(`alarm set successfully: ${time}`);
        } else {
            throw new Error('Failed to set timer');
        }
    } catch (error) {
        console.error('Error:', error);
        setMessage('Failed to connect to server');
    } finally {
        setLoading(false);
        }
    };
    
    return (
        <div className="timer-card">
            <div className="timer-card-header">
                <h2>⏰ 鬧鐘</h2>
            </div>
            <div className="timer-card-body">

                <div className="timer-inputs-container">

                    <div className="hour-column">
                        <button className = "plus-btn"
                        onClick={() => increment(setHours, 23, hours)}>+</button>
                        <input type="number" value={hours} onChange={(e) => handleInputChange(setHours, 23, e.target.value)} />
                        <button className = "minus-btn"
                        onClick={() => decrement(setHours, 23, hours)}>-</button>
                    </div>
                    <span>:</span>
                    <div className="minute-column">
                        <button className = "plus-btn"
                        onClick={() => increment(setMinutes, 59, minutes)}>+</button>
                        <input type="number" value={minutes} onChange={(e) => handleInputChange(setMinutes, 59, e.target.value)} />
                        <button className = "minus-btn"
                        onClick={() => decrement(setMinutes, 59, minutes)}>-</button>
                    </div>
                </div>
        
                {message && <div className="message">{message}</div>}
                
            </div>
            <button className="side-btn" onClick={handleSubmit}>{loading ? 'Setting...' : 'Set Alarm'}</button>
           

            
        </div>
    )
}

export default TimerCard;