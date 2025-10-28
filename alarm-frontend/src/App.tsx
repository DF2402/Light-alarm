import React from "react";
import TimerCard from "./components/TimerCard";
import ClockCard from "./components/ClockCard";
import CameraCard from "./components/CameraCard";
import "./App.css";

function App() {
  const handleTimerSet = (time: string) => {
    console.log('鬧鐘設置為:', time);
  };

  return (
    <div className="App">
      <div className="app-container">
        <h1 className="app-title">⏰ 智能光控鬧鐘系統</h1>
        <TimerCard onTimerSet={handleTimerSet} />
        <ClockCard />
        <CameraCard />
      </div>
    </div>
  );
}

export default App;
