import type { ApplicationAnalytics, ApplicationStats } from "../types";

interface Props {
  stats: ApplicationStats | null;
  analytics?: ApplicationAnalytics | null;
}

const STATUS_META: Record<string, { label: string; color: string }> = {
  applied: { label: "Applied", color: "#2563eb" },
  screening: { label: "Screening", color: "#0891b2" },
  interview: { label: "Interview", color: "#7c3aed" },
  offer: { label: "Offer", color: "#16a34a" },
  rejected: { label: "Rejected", color: "#dc2626" },
};

const STATUS_ORDER = ["applied", "screening", "interview", "offer", "rejected"];

const FUNNEL_META: Record<string, { label: string; color: string }> = {
  applied: { label: "Applied", color: "#2563eb" },
  screening: { label: "Screening", color: "#0891b2" },
  interview: { label: "Interview", color: "#7c3aed" },
  offer: { label: "Offer", color: "#16a34a" },
};

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatWeek(iso: string): string {
  // iso is a YYYY-MM-DD week-start; render as "Jun 22".
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function Dashboard({ stats, analytics }: Props) {
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

      {analytics && analytics.sample_size > 0 && (
        <Funnel analytics={analytics} />
      )}
    </section>
  );
}

function Funnel({ analytics }: { analytics: ApplicationAnalytics }) {
  const top = analytics.funnel[0]?.reached || 1;
  return (
    <div className="dash-charts">
      <div className="dash-chart card">
        <h3>Conversion funnel</h3>
        <div className="funnel">
          {analytics.funnel.map((stage) => {
            const meta = FUNNEL_META[stage.stage] ?? {
              label: stage.stage,
              color: "#64748b",
            };
            return (
              <div className="funnel-row" key={stage.stage}>
                <span className="funnel-label">{meta.label}</span>
                <div className="funnel-track">
                  <div
                    className="funnel-fill"
                    style={{
                      width: `${(stage.reached / top) * 100}%`,
                      background: meta.color,
                    }}
                  >
                    <span className="funnel-count">{stage.reached}</span>
                  </div>
                </div>
                <span className="funnel-pct">{pct(stage.conversion)}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="dash-chart card">
        <h3>Response times</h3>
        <div className="timing-list">
          <Timing
            label="Median time to first response"
            days={analytics.median_days_to_response}
          />
          <Timing
            label="Median time to offer"
            days={analytics.median_days_to_offer}
          />
          <p className="timing-note">
            Derived from the immutable status-change timeline across{" "}
            {analytics.sample_size} application
            {analytics.sample_size === 1 ? "" : "s"}.
          </p>
        </div>
      </div>
    </div>
  );
}

function Timing({ label, days }: { label: string; days: number | null }) {
  return (
    <div className="timing-row">
      <span className="timing-value">
        {days == null ? "—" : `${days} ${days === 1 ? "day" : "days"}`}
      </span>
      <span className="timing-label">{label}</span>
    </div>
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
