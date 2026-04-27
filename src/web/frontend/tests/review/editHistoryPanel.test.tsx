import { describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import { EditHistoryPanel } from "../../src/components/EditHistoryPanel";
import type { EditHistoryEntry } from "../../src/state/reviewStore";

afterEach(() => {
  cleanup();
});

const entries: EditHistoryEntry[] = [
  {
    entry_id: "e1",
    created_at: "2024-01-01T10:00:00.000Z",
    group_count: 3,
    resolved_count: 2,
    unresolved_count: 1,
    trigger_type: "accept",
    compressed: false,
  },
  {
    entry_id: "e2",
    created_at: "2024-01-01T11:00:00.000Z",
    group_count: 3,
    resolved_count: 3,
    unresolved_count: 0,
    trigger_type: "accept",
    compressed: true,
  },
];

describe("EditHistoryPanel (feature 012)", () => {
  it("shows empty-state message when there are no entries", () => {
    render(
      <EditHistoryPanel
        entries={[]}
        selectedEntryId={null}
        restoredEntryId={null}
        busy={false}
        error={null}
        onSelectEntry={() => {}}
        onRestoreEntry={() => {}}
      />,
    );
    expect(screen.getByText(/No history entries yet/i)).toBeTruthy();
  });

  it("renders all supplied history entries", () => {
    render(
      <EditHistoryPanel
        entries={entries}
        selectedEntryId={null}
        restoredEntryId={null}
        busy={false}
        error={null}
        onSelectEntry={() => {}}
        onRestoreEntry={() => {}}
      />,
    );
    const list = screen.getByRole("list", { name: /Edit history entries/i });
    expect(list.querySelectorAll("li").length).toBe(2);
  });

  it("highlights the selected entry with is-selected class", () => {
    render(
      <EditHistoryPanel
        entries={entries}
        selectedEntryId="e1"
        restoredEntryId={null}
        busy={false}
        error={null}
        onSelectEntry={() => {}}
        onRestoreEntry={() => {}}
      />,
    );
    const list = screen.getByRole("list", { name: /Edit history entries/i });
    const rows = list.querySelectorAll("button.edit-history-row");
    expect(rows[0].classList.contains("is-selected")).toBe(true);
    expect(rows[1].classList.contains("is-selected")).toBe(false);
  });

  it("calls onSelectEntry when a row button is clicked", () => {
    const onSelectEntry = vi.fn();
    render(
      <EditHistoryPanel
        entries={entries}
        selectedEntryId={null}
        restoredEntryId={null}
        busy={false}
        error={null}
        onSelectEntry={onSelectEntry}
        onRestoreEntry={() => {}}
      />,
    );
    const list = screen.getByRole("list", { name: /Edit history entries/i });
    const rows = list.querySelectorAll("button.edit-history-row");
    fireEvent.click(rows[0]);
    expect(onSelectEntry).toHaveBeenCalledWith("e1");
  });

  it("calls onRestoreEntry when the Restore snapshot button is clicked", () => {
    const onRestoreEntry = vi.fn();
    render(
      <EditHistoryPanel
        entries={entries}
        selectedEntryId={null}
        restoredEntryId={null}
        busy={false}
        error={null}
        onSelectEntry={() => {}}
        onRestoreEntry={onRestoreEntry}
      />,
    );
    const restoreButtons = screen.getAllByRole("button", { name: /Restore snapshot/i });
    fireEvent.click(restoreButtons[0]);
    expect(onRestoreEntry).toHaveBeenCalledWith("e1");
  });

  it("marks the restored entry with is-restored class", () => {
    render(
      <EditHistoryPanel
        entries={entries}
        selectedEntryId="e1"
        restoredEntryId="e1"
        busy={false}
        error={null}
        onSelectEntry={() => {}}
        onRestoreEntry={() => {}}
      />,
    );
    const list = screen.getByRole("list", { name: /Edit history entries/i });
    const firstRow = list.querySelectorAll("button.edit-history-row")[0];
    expect(firstRow.classList.contains("is-restored")).toBe(true);
  });

  it("shows Compressed badge for compressed entries", () => {
    render(
      <EditHistoryPanel
        entries={entries}
        selectedEntryId={null}
        restoredEntryId={null}
        busy={false}
        error={null}
        onSelectEntry={() => {}}
        onRestoreEntry={() => {}}
      />,
    );
    expect(screen.getByText("Compressed")).toBeTruthy();
  });

  it("shows an error message when error prop is provided", () => {
    render(
      <EditHistoryPanel
        entries={[]}
        selectedEntryId={null}
        restoredEntryId={null}
        busy={false}
        error="Failed to load history"
        onSelectEntry={() => {}}
        onRestoreEntry={() => {}}
      />,
    );
    expect(screen.getByText("Failed to load history")).toBeTruthy();
  });

  it("disables all buttons when busy is true", () => {
    render(
      <EditHistoryPanel
        entries={entries}
        selectedEntryId={null}
        restoredEntryId={null}
        busy={true}
        error={null}
        onSelectEntry={() => {}}
        onRestoreEntry={() => {}}
      />,
    );
    const allButtons = screen.getAllByRole("button");
    for (const button of allButtons) {
      expect((button as HTMLButtonElement).disabled).toBe(true);
    }
  });
});
