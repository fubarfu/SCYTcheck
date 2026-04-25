interface ValidationFeedbackProps {
  type: "success" | "error";
  message: string;
  hint?: string | null;
  conflictGroupId?: string | null;
}

export function ValidationFeedback({
  type,
  message,
  hint = null,
  conflictGroupId = null,
}: ValidationFeedbackProps) {
  return (
    <div
      className={type === "success" ? "validation-feedback validation-feedback-success" : "validation-feedback validation-feedback-error"}
      role={type === "error" ? "alert" : "status"}
      aria-live="polite"
    >
      <p>{message}</p>
      {type === "error" && conflictGroupId ? <small>Conflicts with group {conflictGroupId}</small> : null}
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}
