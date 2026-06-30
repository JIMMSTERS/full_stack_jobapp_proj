interface BlockProps {
  width?: string;
  height?: string;
  radius?: string;
}

/** A single shimmering placeholder block. */
export function Skeleton({ width, height, radius }: BlockProps) {
  return (
    <span
      className="skeleton"
      style={{ width, height, borderRadius: radius }}
    />
  );
}

/** Placeholder for the analytics dashboard KPI row. */
export function DashboardSkeleton() {
  return (
    <div className="dashboard" aria-hidden="true">
      <div className="dash-kpis">
        {Array.from({ length: 6 }).map((_, i) => (
          <div className="card kpi" key={i}>
            <Skeleton width="55%" height="0.7rem" />
            <Skeleton width="40%" height="1.5rem" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Placeholder rows shaped like the applications table. */
export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="card table-skeleton" aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div className="skeleton-row" key={i}>
          <Skeleton width="34%" height="0.95rem" />
          <Skeleton width="26%" height="0.95rem" />
          <Skeleton width="4.5rem" height="1.3rem" radius="999px" />
          <Skeleton width="3rem" height="0.95rem" />
        </div>
      ))}
    </div>
  );
}

/** Placeholder columns shaped like the Kanban board. */
export function BoardSkeleton() {
  return (
    <div className="kanban" aria-hidden="true">
      {Array.from({ length: 5 }).map((_, col) => (
        <div className="kanban-col" key={col}>
          <div className="kanban-col-head">
            <Skeleton width="55%" height="0.8rem" />
            <Skeleton width="1.4rem" height="1rem" radius="999px" />
          </div>
          <div className="kanban-col-body">
            {Array.from({ length: 2 }).map((_, card) => (
              <div className="kanban-card skeleton-card" key={card}>
                <Skeleton width="70%" height="0.85rem" />
                <Skeleton width="50%" height="0.75rem" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
