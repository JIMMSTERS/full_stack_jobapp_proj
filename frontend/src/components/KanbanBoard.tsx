import { useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import type { Application } from "../types";
import { STATUSES } from "../types";

interface Props {
  applications: Application[];
  onStatusChange: (id: number, status: string) => void;
  onOpenDetail: (application: Application) => void;
}

const STATUS_LABELS: Record<string, string> = {
  applied: "Applied",
  screening: "Screening",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
};

function CardContent({ app }: { app: Application }) {
  return (
    <>
      <div className="kanban-card-company">
        {app.company}
        {app.source === "gmail" && (
          <span className="badge badge-source" title="Imported from Gmail">
            Gmail
          </span>
        )}
      </div>
      <div className="kanban-card-position">{app.position}</div>
    </>
  );
}

function Card({
  app,
  onOpenDetail,
}: {
  app: Application;
  onOpenDetail: (application: Application) => void;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: app.id,
  });
  return (
    <div
      ref={setNodeRef}
      className={`kanban-card${isDragging ? " is-dragging" : ""}`}
      onClick={() => onOpenDetail(app)}
      {...listeners}
      {...attributes}
    >
      <CardContent app={app} />
    </div>
  );
}

function Column({
  status,
  apps,
  onOpenDetail,
}: {
  status: string;
  apps: Application[];
  onOpenDetail: (application: Application) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  return (
    <div
      ref={setNodeRef}
      className={`kanban-col${isOver ? " is-over" : ""}`}
    >
      <div className="kanban-col-head">
        <span className={`kanban-col-title kanban-dot-${status}`}>
          {STATUS_LABELS[status] ?? status}
        </span>
        <span className="kanban-col-count">{apps.length}</span>
      </div>
      <div className="kanban-col-body">
        {apps.map((a) => (
          <Card key={a.id} app={a} onOpenDetail={onOpenDetail} />
        ))}
        {apps.length === 0 && <div className="kanban-empty">Drop here</div>}
      </div>
    </div>
  );
}

export function KanbanBoard({ applications, onStatusChange, onOpenDetail }: Props) {
  const [activeApp, setActiveApp] = useState<Application | null>(null);
  // Require a small drag distance so clicks/taps don't start a drag.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  function onDragStart(event: DragStartEvent) {
    const app = applications.find((a) => a.id === Number(event.active.id));
    setActiveApp(app ?? null);
  }

  function onDragEnd(event: DragEndEvent) {
    setActiveApp(null);
    const { active, over } = event;
    if (!over) return;
    const id = Number(active.id);
    const newStatus = String(over.id);
    const app = applications.find((a) => a.id === id);
    if (app && app.status !== newStatus) {
      onStatusChange(id, newStatus);
    }
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onDragCancel={() => setActiveApp(null)}
    >
      <div className="kanban">
        {STATUSES.map((status) => (
          <Column
            key={status}
            status={status}
            apps={applications.filter((a) => a.status === status)}
            onOpenDetail={onOpenDetail}
          />
        ))}
      </div>
      <DragOverlay>
        {activeApp ? (
          <div className="kanban-card is-overlay">
            <CardContent app={activeApp} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
