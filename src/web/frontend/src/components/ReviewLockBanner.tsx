interface ReviewLockBannerProps {
  readonly: boolean;
  ownerSessionId: string | null;
  currentSessionId: string | null;
}

export function ReviewLockBanner({ readonly, ownerSessionId, currentSessionId }: ReviewLockBannerProps) {
  if (!readonly) {
    return null;
  }

  const ownerLabel = ownerSessionId
    ? `Session ${ownerSessionId.slice(0, 8)}`
    : "another session";

  return (
    <section className="review-lock-banner" role="alert">
      <h3>Read-only mode enabled</h3>
      <p>
        This workspace is currently locked by {ownerLabel}. Mutations are disabled for this session
        {currentSessionId ? ` (${currentSessionId.slice(0, 8)}).` : "."}
      </p>
    </section>
  );
}
