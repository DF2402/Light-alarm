import React from "react";
import TimerCard from "./components/TimerCard";
import ClockCard from "./components/ClockCard";
import CameraCard from "./components/CameraCard";
import IotCard from "./components/IotCard";
import "./App.css";

function App() {
  const handleTimerSet = (time: string) => {
    console.log("Timer set to:", time);
  };

  return (
    <div className="App">
      <div className="app-container">
        <h1 className="app-title">Smart Light Control Alarm System</h1>
        <TimerCard onTimerSet={handleTimerSet} />
        <ClockCard />
        <CameraCard />
        <IotCard />
      </div>
    </div>
  );
}

export default App;
