import { useEffect, useState } from "react";
import { ThemeToggle } from "./components/ThemeToggle";
import { AnalysisPage } from "./pages/AnalysisPage";
import { HistoryPage } from "./pages/HistoryPage";
import { MainLayout } from "./pages/MainLayout";
import { ReviewPage } from "./pages/ReviewPage";
import { hydrateFromReopen, initialReviewStoreState } from "./state/reviewStore";
import type { ReopenResponse } from "./state/historyStore";

type ViewMode = "analysis" | "review" | "videos";

export function App() {
  const [view, setView] = useState<ViewMode>("analysis");
  const [reviewStore, setReviewStore] = useState(initialReviewStoreState);
  const [lastReopenPayload, setLastReopenPayload] = useState<ReopenResponse | null>(null);
  const [lastReviewCsvPath, setLastReviewCsvPath] = useState<string>("");

  useEffect(() => {
    const captureOpenReview = (event: Event) => {
      const custom = event as CustomEvent<{ csvPath?: string }>;
      const csvPath = custom.detail?.csvPath?.trim();
      if (csvPath) {
        setLastReviewCsvPath(csvPath);
      }
    };
    window.addEventListener("scyt:open-review", captureOpenReview as EventListener);
    return () => window.removeEventListener("scyt:open-review", captureOpenReview as EventListener);
  }, []);

  const handleReopenToReview = (payload: ReopenResponse) => {
    setLastReopenPayload(payload);
    setReviewStore((prev) => hydrateFromReopen(prev, payload));
    window.dispatchEvent(new CustomEvent("scyt:history-reopen", { detail: payload }));
    const reopenCsvPath = payload.derived_results.primary_csv_path
      ?? payload.derived_results.resolved_csv_paths[0]
      ?? null;
    if (reopenCsvPath) {
      window.dispatchEvent(
        new CustomEvent("scyt:open-review", {
          detail: { csvPath: reopenCsvPath, autoLoad: true },
        }),
      );
    }
    setView("review");
  };

  return (
    <MainLayout
      view={view}
      onViewChange={setView}
      onOpenSettings={() => setView("videos")}
      rightSlot={<ThemeToggle />}
    >
      {view === "analysis" && <AnalysisPage reopenPayload={lastReopenPayload} />}
      {view === "review" && (
        <ReviewPage reopenContext={reviewStore.reopenContext} autoCsvPath={lastReviewCsvPath} />
      )}
      {view === "videos" && <HistoryPage onReopenToReview={handleReopenToReview} />}
    </MainLayout>
  );
}
