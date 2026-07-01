import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApplicationTable } from "./ApplicationTable";
import type { Application } from "../types";

function makeApp(overrides: Partial<Application> = {}): Application {
  return {
    id: 1,
    company: "Acme",
    position: "Engineer",
    status: "applied",
    url: null,
    notes: null,
    follow_up_date: null,
    source: "manual",
    created_at: "2026-01-01T00:00:00",
    updated_at: "2026-01-01T00:00:00",
    ...overrides,
  };
}

const noop = () => {};

function renderTable(apps: Application[], props: Partial<Parameters<typeof ApplicationTable>[0]> = {}) {
  return render(
    <ApplicationTable
      applications={apps}
      onDelete={props.onDelete ?? noop}
      onStatusChange={props.onStatusChange ?? noop}
      onOpenDetail={props.onOpenDetail ?? noop}
      highlightId={props.highlightId ?? null}
    />
  );
}

describe("ApplicationTable", () => {
  it("shows an empty state when there are no applications", () => {
    renderTable([]);
    expect(screen.getByText(/no applications yet/i)).toBeInTheDocument();
  });

  it("renders a row per application", () => {
    renderTable([
      makeApp({ id: 1, company: "Acme" }),
      makeApp({ id: 2, company: "Globex" }),
    ]);
    expect(screen.getByText("Acme")).toBeInTheDocument();
    expect(screen.getByText("Globex")).toBeInTheDocument();
  });

  it("filters rows by the search query", async () => {
    const user = userEvent.setup();
    renderTable([
      makeApp({ id: 1, company: "Acme" }),
      makeApp({ id: 2, company: "Globex" }),
    ]);

    await user.type(screen.getByLabelText(/search applications/i), "glob");

    expect(screen.queryByText("Acme")).not.toBeInTheDocument();
    expect(screen.getByText("Globex")).toBeInTheDocument();
  });

  it("filters rows when a status chip is selected", async () => {
    const user = userEvent.setup();
    renderTable([
      makeApp({ id: 1, company: "Acme", status: "applied" }),
      makeApp({ id: 2, company: "Globex", status: "interview" }),
    ]);

    const filters = screen.getByRole("group", { name: /filter by status/i });
    await user.click(within(filters).getByRole("button", { name: /interview/i }));

    expect(screen.queryByText("Acme")).not.toBeInTheDocument();
    expect(screen.getByText("Globex")).toBeInTheDocument();
  });

  it("shows an overdue follow-up pill", () => {
    renderTable([makeApp({ company: "Acme", status: "applied", follow_up_date: "2020-01-01" })]);
    expect(screen.getByText(/overdue/i)).toBeInTheDocument();
  });

  it("calls onOpenDetail when a company name is clicked", async () => {
    const user = userEvent.setup();
    const onOpenDetail = vi.fn();
    renderTable([makeApp({ id: 7, company: "Acme" })], { onOpenDetail });

    await user.click(screen.getByRole("button", { name: "Acme" }));

    expect(onOpenDetail).toHaveBeenCalledTimes(1);
    expect(onOpenDetail).toHaveBeenCalledWith(expect.objectContaining({ id: 7 }));
  });

  it("calls onDelete when the delete action is clicked", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    renderTable([makeApp({ id: 9, company: "Acme" })], { onDelete });

    await user.click(screen.getByRole("button", { name: /delete/i }));

    expect(onDelete).toHaveBeenCalledWith(9);
  });
});
