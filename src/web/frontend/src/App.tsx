import { useState } from "react";
import { ThemeToggle } from "./components/ThemeToggle";
import { AnalysisPage } from "./pages/AnalysisPage";
import { HistoryPage } from "./pages/HistoryPage";
import { ReviewPage } from "./pages/ReviewPage";
import { hydrateFromReopen, initialReviewStoreState } from "./state/reviewStore";
import type { ReopenResponse } from "./state/historyStore";

type ViewMode = "analysis" | "review" | "history";

export function App() {
  const [view, setView] = useState<ViewMode>("analysis");
  const [reviewStore, setReviewStore] = useState(initialReviewStoreState);

  const handleReopenToReview = (payload: ReopenResponse) => {
    setReviewStore((prev) => hydrateFromReopen(prev, payload));
    window.dispatchEvent(new CustomEvent("scyt:history-reopen", { detail: payload }));
    if (payload.derived_results.primary_csv_path) {
      window.dispatchEvent(
        new CustomEvent("scyt:open-review", {
          detail: { csvPath: payload.derived_results.primary_csv_path, autoLoad: true },
        }),
      );
    }
    setView("review");
  };

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
            <button
              type="button"
              className={`app-nav-link${view === "history" ? " active" : ""}`}
              onClick={() => setView("history")}
            >
              History
            </button>
          </nav>
        </div>
        <ThemeToggle />
      </header>
      {view === "analysis" && <AnalysisPage />}
      {view === "review" && <ReviewPage reopenContext={reviewStore.reopenContext} />}
      {view === "history" && <HistoryPage onReopenToReview={handleReopenToReview} />}
    </main>
  );
}
