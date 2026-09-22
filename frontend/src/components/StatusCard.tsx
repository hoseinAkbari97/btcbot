interface Props {
  label: string;
  value: string;
  state: "up" | "down" | "unknown";
  detail: string;
}

export function StatusCard({ label, value, state, detail }: Props) {
  return (
    <article className="status-card panel">
      <div className="status-heading">
        <span>{label}</span>
        <i className={`status-dot ${state}`} />
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

