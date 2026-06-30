export type FollowUpTone = "overdue" | "soon" | "later";

export interface FollowUp {
  label: string;
  tone: FollowUpTone;
}

const CLOSED_STATUSES = new Set(["offer", "rejected"]);

/**
 * Describe an application's follow-up date relative to today.
 *
 * Returns ``null`` when there is no date or the application is already closed
 * (offer/rejected), since a reminder is no longer actionable. Otherwise it
 * yields a short human label and an urgency ``tone`` used for colour coding.
 */
export function getFollowUp(
  date: string | null,
  status: string
): FollowUp | null {
  if (!date || CLOSED_STATUSES.has(status)) return null;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(`${date}T00:00:00`);
  const days = Math.round((due.getTime() - today.getTime()) / 86_400_000);

  if (days < 0) {
    return {
      label: days === -1 ? "1 day overdue" : `${-days} days overdue`,
      tone: "overdue",
    };
  }
  if (days === 0) return { label: "Due today", tone: "soon" };
  if (days === 1) return { label: "Due tomorrow", tone: "soon" };
  if (days <= 3) return { label: `Due in ${days} days`, tone: "soon" };

  return {
    label: `Due ${due.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    })}`,
    tone: "later",
  };
}
