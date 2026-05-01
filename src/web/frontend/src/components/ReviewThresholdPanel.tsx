interface Props {
  similarityThreshold: number;
  recommendationThreshold: number;
  onChange: (values: {
    similarityThreshold: number;
    recommendationThreshold: number;
  }) => void;
}

export function ReviewThresholdPanel({
  similarityThreshold,
  recommendationThreshold,
  onChange,
}: Props) {
  return (
    <div className="review-threshold-panel">
      <label>
        Similarity threshold
        <input
          type="range"
          min={0}
          max={100}
          value={similarityThreshold}
          onChange={(e) =>
            onChange({
              similarityThreshold: Number(e.target.value),
              recommendationThreshold,
            })
          }
        />
        <span>{similarityThreshold}</span>
      </label>

      <label>
        Recommendation threshold
        <input
          type="range"
          min={0}
          max={100}
          value={recommendationThreshold}
          onChange={(e) =>
            onChange({
              similarityThreshold,
              recommendationThreshold: Number(e.target.value),
            })
          }
        />
        <span>{recommendationThreshold}</span>
      </label>
    </div>
  );
}
