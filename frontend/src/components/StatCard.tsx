interface StatCardProps {
  label: string;
  value: string;
  hint: string;
  tone?: 'light' | 'dark';
}

export function StatCard({ label, value, hint, tone = 'light' }: StatCardProps) {
  return (
    <div className={`stat-card ${tone === 'dark' ? 'stat-card-dark' : ''}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{hint}</span>
    </div>
  );
}
