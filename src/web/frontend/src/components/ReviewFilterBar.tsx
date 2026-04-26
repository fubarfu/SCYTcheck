interface Props {
  searchText: string;
  status: "all" | "pending" | "confirmed" | "rejected";
  onSearchTextChange: (value: string) => void;
  onStatusChange: (value: "all" | "pending" | "confirmed" | "rejected") => void;
}

export function ReviewFilterBar({
  searchText,
  status,
  onSearchTextChange,
  onStatusChange,
}: Props) {
  return (
    <div className="review-filter-bar">
      <input
        type="text"
        value={searchText}
        onChange={(e) => onSearchTextChange(e.target.value)}
        placeholder="Search candidates..."
        aria-label="Search candidates"
      />
      <select
        value={status}
        onChange={(e) => onStatusChange(e.target.value as Props["status"])}
        aria-label="Filter by status"
      >
        <option value="all">All</option>
        <option value="pending">Pending</option>
        <option value="confirmed">Confirmed</option>
        <option value="rejected">Rejected</option>
      </select>
    </div>
  );
}
