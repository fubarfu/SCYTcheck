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
        <div className="app-nav-left">
          <h1>SCYTcheck</h1>
          <nav className="app-nav-links">
            <button
              type="button"
              className={`app-nav-link${view === "analysis" ? " active" : ""}`}
              onClick={() => setView("analysis")}
            >
              Analysis
            </button>
            <button
              type="button"
              className={`app-nav-link${view === "review" ? " active" : ""}`}
              onClick={() => setView("review")}
            >
              Review
            </button>
          </nav>
        </div>
        <ThemeToggle />
      </header>
      {view === "analysis" ? <AnalysisPage /> : <ReviewPage />}
    </main>
  );
}
