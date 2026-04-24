interface Props {
  message: string;
  onRetry?: () => void;
}

export function SessionLoadErrorState({ message, onRetry }: Props) {
  return (
    <div className="session-load-error" role="alert">
      <h4>Unable to load session</h4>
      <p>{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
