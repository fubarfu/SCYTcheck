import { useEffect, useState } from "react";
import { ThemeToggle } from "./components/ThemeToggle";
import { AnalysisPage } from "./pages/AnalysisPage";
import { HistoryPage } from "./pages/HistoryPage";
import { MainLayout } from "./pages/MainLayout";
import { ReviewPage } from "./pages/ReviewPage";
import { hydrateFromReopen, initialReviewStoreState } from "./state/reviewStore";
import type { ReopenResponse } from "./state/historyStore";

type ViewMode = "analysis" | "review" | "videos";

function getViewFromHash(): ViewMode {
  if (typeof window === "undefined") {
    return "analysis";
  }

  const hash = window.location.hash;
  if (hash.startsWith("#/review")) {
    return "review";
  }
  if (hash.startsWith("#/videos")) {
    return "videos";
  }
  return "analysis";
}

function setHashForView(view: ViewMode) {
  if (typeof window === "undefined") {
    return;
  }

  if (view === "review" && window.location.hash.startsWith("#/review")) {
    return;
  }

  const nextHash = view === "videos" ? "#/videos" : view === "review" ? "#/review" : "#/analysis";
  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash;
  }
}

export function App() {
  const [view, setView] = useState<ViewMode>(() => getViewFromHash());
  const [reviewStore, setReviewStore] = useState(initialReviewStoreState);
  const [lastReopenPayload, setLastReopenPayload] = useState<ReopenResponse | null>(null);
  const [lastReviewCsvPath, setLastReviewCsvPath] = useState<string>("");

  useEffect(() => {
    const syncViewFromHash = () => {
      setView(getViewFromHash());
    };

    syncViewFromHash();
    window.addEventListener("hashchange", syncViewFromHash);

    const captureOpenReview = (event: Event) => {
      const custom = event as CustomEvent<{ csvPath?: string }>;
      const csvPath = custom.detail?.csvPath?.trim();
      if (csvPath) {
        setLastReviewCsvPath(csvPath);
      }
      setHashForView("review");
      setView("review");
    };
    window.addEventListener("scyt:open-review", captureOpenReview as EventListener);

    return () => {
      window.removeEventListener("hashchange", syncViewFromHash);
      window.removeEventListener("scyt:open-review", captureOpenReview as EventListener);
    };
  }, []);

  const handleViewChange = (nextView: ViewMode) => {
    setHashForView(nextView);
    setView(nextView);
  };

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
    setHashForView("review");
    setView("review");
  };

  return (
    <MainLayout
      view={view}
      onViewChange={handleViewChange}
      onOpenSettings={() => handleViewChange("videos")}
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
