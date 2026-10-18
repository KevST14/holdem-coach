import { useState } from "react";
import Play from "./components/Play";
import Learn from "./components/Learn";

type Tab = "play" | "learn";

export default function App() {
  const [tab, setTab] = useState<Tab>("learn");

  return (
    <div className="app">
      <header className="topbar">
        <h1 className="brand">
          <span aria-hidden="true">♠</span> Hold'em Coach
        </h1>
        <nav className="tabs" aria-label="Sections">
          <button className={tab === "learn" ? "tab active" : "tab"} onClick={() => setTab("learn")}>
            Learn
          </button>
          <button className={tab === "play" ? "tab active" : "tab"} onClick={() => setTab("play")}>
            Play
          </button>
        </nav>
      </header>
      <main>
        {/* Keep Play mounted so switching tabs doesn't lose the game in progress. */}
        <div hidden={tab !== "play"}>
          <Play />
        </div>
        {tab === "learn" && <Learn onStartPlaying={() => setTab("play")} />}
      </main>
    </div>
  );
}
