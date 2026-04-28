import type { ReactNode } from "react";

type ViewMode = "analysis" | "review" | "videos";

type MainLayoutProps = {
  view: ViewMode;
  onViewChange: (view: ViewMode) => void;
  onOpenSettings: () => void;
  rightSlot?: ReactNode;
  children: ReactNode;
};

export function MainLayout({
  view,
  onViewChange,
  onOpenSettings,
  rightSlot,
  children,
}: MainLayoutProps) {
  return (
    <main className="app-shell">
      <header className="app-nav">
        <div className="app-nav-left">
          <h1>SCYTcheck</h1>
          <nav className="app-nav-links">
            <button
              type="button"
              className={`app-nav-link${view === "analysis" ? " active" : ""}`}
              onClick={() => onViewChange("analysis")}
            >
              Analysis
            </button>
            <button
              type="button"
              className={`app-nav-link${view === "review" ? " active" : ""}`}
              onClick={() => onViewChange("review")}
            >
              Review
            </button>
            <button
              type="button"
              className={`app-nav-link${view === "videos" ? " active" : ""}`}
              onClick={() => onViewChange("videos")}
            >
              Videos
            </button>
            <button
              type="button"
              className="app-nav-link app-nav-gear"
              onClick={onOpenSettings}
              aria-label="Open Settings"
              title="Settings"
            >
              ⚙
            </button>
          </nav>
        </div>
        {rightSlot}
      </header>
      {children}
    </main>
  );
}
