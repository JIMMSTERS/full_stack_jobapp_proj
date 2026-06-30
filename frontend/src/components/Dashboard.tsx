import type { ApplicationStats } from "../types";

interface Props {
  stats: ApplicationStats | null;
}

const STATUS_META: Record<string, { label: string; color: string }> = {
  applied: { label: "Applied", color: "#2563eb" },
  screening: { label: "Screening", color: "#0891b2" },
  interview: { label: "Interview", color: "#7c3aed" },
  offer: { label: "Offer", color: "#16a34a" },
  rejected: { label: "Rejected", color: "#dc2626" },
};

const STATUS_ORDER = ["applied", "screening", "interview", "offer", "rejected"];

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatWeek(iso: string): string {
  // iso is a YYYY-MM-DD week-start; render as "Jun 22".
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function Dashboard({ stats }: Props) {
  if (!stats || stats.total === 0) {
    return null;
  }

  const maxStatus = Math.max(
    ...STATUS_ORDER.map((s) => stats.by_status[s] ?? 0),
    1
  );
  const maxWeek = Math.max(...stats.weekly.map((w) => w.count), 1);

  return (
    <section className="dashboard">
      <div className="dash-kpis">
        <Kpi label="Total applications" value={stats.total} accent="#0f172a" />
        <Kpi
          label="Active"
          value={stats.active}
          accent="#2563eb"
          sub="in progress"
        />
        <Kpi
          label="Response rate"
          value={pct(stats.response_rate)}
          accent="#0891b2"
          sub={`${stats.responded} responded`}
        />
        <Kpi
          label="Interview rate"
          value={pct(stats.interview_rate)}
          accent="#7c3aed"
          sub="reached interview"
        />
        <Kpi
          label="Offers"
          value={stats.offers}
          accent="#16a34a"
          sub={pct(stats.offer_rate)}
        />
        <Kpi
          label="This week"
          value={stats.this_week}
          accent="#ea580c"
          sub="new applications"
        />
      </div>

      <div className="dash-charts">
        <div className="dash-chart card">
          <h3>Pipeline by status</h3>
          <div className="bar-list">
            {STATUS_ORDER.map((status) => {
              const count = stats.by_status[status] ?? 0;
              const meta = STATUS_META[status];
              const share = stats.total ? count / stats.total : 0;
              return (
                <div className="bar-row" key={status}>
                  <span className="bar-label">{meta.label}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(count / maxStatus) * 100}%`,
                        background: meta.color,
                      }}
                    />
                  </div>
                  <span className="bar-value">
                    {count}
                    <span className="bar-share">{pct(share)}</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="dash-chart card">
          <h3>Applications over time</h3>
          <div className="spark">
            {stats.weekly.map((point) => (
              <div
                className="spark-col"
                key={point.week}
                title={`${point.count} in week of ${point.week}`}
              >
                <div className="spark-bar-wrap">
                  <div
                    className="spark-bar"
                    style={{ height: `${(point.count / maxWeek) * 100}%` }}
                  >
                    {point.count > 0 && (
                      <span className="spark-count">{point.count}</span>
                    )}
                  </div>
                </div>
                <span className="spark-x">{formatWeek(point.week)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

interface KpiProps {
  label: string;
  value: number | string;
  accent: string;
  sub?: string;
}

function Kpi({ label, value, accent, sub }: KpiProps) {
  return (
    <div className="kpi card">
      <div className="kpi-value" style={{ color: accent }}>
        {value}
      </div>
      <div className="kpi-label">{label}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}
