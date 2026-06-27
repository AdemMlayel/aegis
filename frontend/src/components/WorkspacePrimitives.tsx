import type { ReactNode } from "react";

export function TabButton({
  active,
  icon,
  label,
  onClick
}: {
  active: boolean;
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return <button className={active ? "active" : ""} onClick={onClick}>{icon}{label}</button>;
}

export function StatusPill({ value }: { value: string }) {
  return <span className={`status-pill ${value}`}>{value.replaceAll("_", " ")}</span>;
}

export function Metric({ label, value }: { label: string; value: string }) {
  return <div className="deliverable-metric"><span>{label}</span><strong>{value}</strong></div>;
}

export function ValidationMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="validation-metric">
      <div><span>{label}</span><strong>{value}%</strong></div>
      <span className="metric-track"><span style={{ width: `${value}%` }} /></span>
    </div>
  );
}

export function BulletList({ items }: { items: string[] }) {
  return items.length ? <ul className="bullet-list">{items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : null;
}

export function DetailSection({
  title,
  items,
  ordered = false
}: {
  title: string;
  items: string[];
  ordered?: boolean;
}) {
  const List = ordered ? "ol" : "ul";
  return (
    <section className="detail-section">
      <h3>{title}</h3>
      {items.length ? <List>{items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</List> : <p className="muted-copy">None recorded.</p>}
    </section>
  );
}

export function EmptyView({ icon, text }: { icon: ReactNode; text: string }) {
  return <div className="view-empty"><span>{icon}</span><p>{text}</p></div>;
}
