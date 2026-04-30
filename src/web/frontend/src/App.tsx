import { useEffect, useState } from "react";
import { ThemeToggle } from "./components/ThemeToggle";
import { AnalysisPage } from "./pages/AnalysisPage";
import { MainLayout } from "./pages/MainLayout";
import { ReviewPage } from "./pages/ReviewPage";
import { SettingsPage } from "./pages/SettingsPage";
import { VideosPage } from "./pages/VideosPage";
import { hydrateFromReopen, initialReviewStoreState } from "./state/reviewStore";
import type { ReopenResponse } from "./state/historyStore";

type ViewMode = "analysis" | "review" | "videos" | "settings";
const REVIEW_HASH_STORAGE_KEY = "scyt:last-review-hash";

function getViewFromHash(): ViewMode {
  if (typeof window === "undefined") {
    return "analysis";
  }

  const hash = window.location.hash;
  if (hash.startsWith("#/review")) {
    return "review";
  }
  if (hash.startsWith("#/settings")) {
    return "settings";
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

  const nextHash =
    view === "videos"
      ? "#/videos"
      : view === "settings"
        ? "#/settings"
        : view === "review"
          ? "#/review"
          : "#/analysis";
  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash;
  }
}

function normalizeReviewHash(hash: string | null | undefined): string {
  const trimmed = (hash ?? "").trim();
  return trimmed.startsWith("#/review") ? trimmed : "#/review";
}

function readLastReviewHash(): string {
  if (typeof window === "undefined") {
    return "#/review";
  }
  const stored = window.sessionStorage.getItem(REVIEW_HASH_STORAGE_KEY);
  return normalizeReviewHash(stored ?? window.location.hash);
}

function writeLastReviewHash(hash: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.setItem(REVIEW_HASH_STORAGE_KEY, normalizeReviewHash(hash));
}

export function App() {
  const [view, setView] = useState<ViewMode>(() => getViewFromHash());
  const [lastReviewHash, setLastReviewHash] = useState<string>(() => readLastReviewHash());
  const [reviewStore, setReviewStore] = useState(initialReviewStoreState);
  const [lastReopenPayload, setLastReopenPayload] = useState<ReopenResponse | null>(null);
  const [lastReviewCsvPath, setLastReviewCsvPath] = useState<string>("");

  useEffect(() => {
    const syncViewFromHash = () => {
      if (window.location.hash.startsWith("#/review")) {
        const nextHash = normalizeReviewHash(window.location.hash);
        writeLastReviewHash(nextHash);
        setLastReviewHash(nextHash);
      }
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
      const nextReviewHash = normalizeReviewHash(window.location.hash);
      writeLastReviewHash(nextReviewHash);
      setLastReviewHash(nextReviewHash);
      if (window.location.hash !== nextReviewHash) {
        window.location.hash = nextReviewHash;
      }
      setView("review");
    };
    window.addEventListener("scyt:open-review", captureOpenReview as EventListener);

    return () => {
      window.removeEventListener("hashchange", syncViewFromHash);
      window.removeEventListener("scyt:open-review", captureOpenReview as EventListener);
    };
  }, []);

  const handleViewChange = (nextView: ViewMode) => {
    if (nextView !== "review" && window.location.hash.startsWith("#/review")) {
      const currentReviewHash = normalizeReviewHash(window.location.hash);
      writeLastReviewHash(currentReviewHash);
      setLastReviewHash(currentReviewHash);
    }

    if (nextView === "review") {
      const nextHash = normalizeReviewHash(readLastReviewHash() || lastReviewHash);
      if (window.location.hash !== nextHash) {
        window.location.hash = nextHash;
      }
    } else {
      setHashForView(nextView);
    }
    setView(nextView);
  };

  return (
    <MainLayout
      view={view}
      onViewChange={handleViewChange}
      onOpenSettings={() => handleViewChange("settings")}
      rightSlot={<ThemeToggle />}
    >
      {view === "analysis" && <AnalysisPage reopenPayload={lastReopenPayload} />}
      {view === "review" && (
        <ReviewPage reopenContext={reviewStore.reopenContext} autoCsvPath={lastReviewCsvPath} />
      )}
      {view === "videos" && <VideosPage />}
      {view === "settings" && <SettingsPage />}
    </MainLayout>
  );
}
