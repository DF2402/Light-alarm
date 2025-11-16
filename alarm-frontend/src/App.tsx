import React from "react";
import TimerCard from "./components/TimerCard";
import ClockCard from "./components/ClockCard";
import CameraCard from "./components/CameraCard";
import IotCard from "./components/IotCard";
import "./App.css";
import GraphCard from "./components/GraphCard";
import LastDetection from "./components/LastDetection";

function App() {
  const handleTimerSet = (time: string) => {
    console.log("Timer set to:", time);
  };

  return (
    <div className="App">
      <h1 className="app-title">Smart Light Control Alarm System</h1>
      <div className="app-container">
        <TimerCard onTimerSet={handleTimerSet} />
        <ClockCard />
        <CameraCard />
        <IotCard />
        <GraphCard deviceId="alarm-clock" />
        <LastDetection />
      </div>
    </div>
  );
}

export default App;
