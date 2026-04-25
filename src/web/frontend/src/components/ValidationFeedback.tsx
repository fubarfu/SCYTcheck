interface ValidationFeedbackProps {
  type: "success" | "error";
  message: string;
  hint?: string | null;
}

export function ValidationFeedback({ type, message, hint = null }: ValidationFeedbackProps) {
  return (
    <div
      className={type === "success" ? "validation-feedback validation-feedback-success" : "validation-feedback validation-feedback-error"}
      role={type === "error" ? "alert" : "status"}
      aria-live="polite"
    >
      <p>{message}</p>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}
