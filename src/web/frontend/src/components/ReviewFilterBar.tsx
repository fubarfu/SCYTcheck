interface Props {
  searchText: string;
  status: "all" | "pending" | "confirmed" | "rejected";
  similarityThreshold: number;
  recommendationThreshold: number;
  onSearchTextChange: (value: string) => void;
  onStatusChange: (value: "all" | "pending" | "confirmed" | "rejected") => void;
  onSimilarityThresholdChange: (value: number) => void;
  onRecommendationThresholdChange: (value: number) => void;
}

export function ReviewFilterBar({
  searchText,
  status,
  similarityThreshold,
  recommendationThreshold,
  onSearchTextChange,
  onStatusChange,
  onSimilarityThresholdChange,
  onRecommendationThresholdChange,
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
      <label className="review-threshold-control">
        <span>Group Similarity</span>
        <div>
          <input
            type="range"
            min={50}
            max={100}
            value={similarityThreshold}
            onChange={(e) => onSimilarityThresholdChange(Number(e.target.value))}
            aria-label="Group Similarity"
          />
          <strong>{similarityThreshold}%</strong>
        </div>
      </label>
      <label className="review-threshold-control">
        <span>Recommendations</span>
        <div>
          <input
            type="range"
            min={0}
            max={100}
            value={recommendationThreshold}
            onChange={(e) => onRecommendationThresholdChange(Number(e.target.value))}
            aria-label="Recommendation threshold"
          />
          <strong>{recommendationThreshold}</strong>
        </div>
      </label>
        <option value="pending">Pending</option>
        <option value="confirmed">Confirmed</option>
        <option value="rejected">Rejected</option>
      </select>
    </div>
  );
}
