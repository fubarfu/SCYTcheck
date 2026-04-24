import { useState } from "react";
import { ThemeToggle } from "./components/ThemeToggle";
import { AnalysisPage } from "./pages/AnalysisPage";
import { ReviewPage } from "./pages/ReviewPage";

type ViewMode = "analysis" | "review";

export function App() {
  const [view, setView] = useState<ViewMode>("analysis");

  return (
    <main className="app-shell">
      <header className="app-nav">
        <h1>SCYTcheck</h1>
        <div className="app-nav-actions">
          <ThemeToggle />
          <button className={view === "analysis" ? "active" : ""} onClick={() => setView("analysis")}>
            Analysis
          </button>
          <button className={view === "review" ? "active" : ""} onClick={() => setView("review")}>
            Review
          </button>
        </div>
      </header>
      {view === "analysis" ? <AnalysisPage /> : <ReviewPage />}
    </main>
  );
}
