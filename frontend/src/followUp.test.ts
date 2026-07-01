import { describe, expect, it } from "vitest";
import { getFollowUp } from "./followUp";

/** Build a YYYY-MM-DD string offset from today by `days` (local time). */
function dayOffset(days: number): string {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + days);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

describe("getFollowUp", () => {
  it("returns null when there is no date", () => {
    expect(getFollowUp(null, "applied")).toBeNull();
  });

  it("returns null for closed applications even with a date", () => {
    expect(getFollowUp(dayOffset(-2), "offer")).toBeNull();
    expect(getFollowUp(dayOffset(2), "rejected")).toBeNull();
  });

  it("marks a past date as overdue", () => {
    expect(getFollowUp(dayOffset(-1), "applied")).toEqual({
      label: "1 day overdue",
      tone: "overdue",
    });
    expect(getFollowUp(dayOffset(-3), "applied")).toEqual({
      label: "3 days overdue",
      tone: "overdue",
    });
  });

  it("labels today and tomorrow as soon", () => {
    expect(getFollowUp(dayOffset(0), "screening")).toEqual({
      label: "Due today",
      tone: "soon",
    });
    expect(getFollowUp(dayOffset(1), "screening")).toEqual({
      label: "Due tomorrow",
      tone: "soon",
    });
  });

  it("labels 2-3 days out as soon with a day count", () => {
    expect(getFollowUp(dayOffset(3), "interview")).toEqual({
      label: "Due in 3 days",
      tone: "soon",
    });
  });

  it("labels dates more than 3 days out as later", () => {
    const result = getFollowUp(dayOffset(10), "applied");
    expect(result?.tone).toBe("later");
    expect(result?.label).toMatch(/^Due /);
  });
});
