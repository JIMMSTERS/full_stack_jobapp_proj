import { useEffect, useMemo, useRef, useState } from "react";
import type { Application } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  applications: Application[];
  onAddApplication: () => void;
  onGoToGmail: () => void;
  onJumpTo: (id: number) => void;
  onSignOut: () => void;
}

interface Command {
  id: string;
  label: string;
  group: string;
  hint?: string;
  keywords: string;
  run: () => void;
}

export function CommandPalette({
  open,
  onClose,
  applications,
  onAddApplication,
  onGoToGmail,
  onJumpTo,
  onSignOut,
}: Props) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: Command[] = useMemo(() => {
    const actions: Command[] = [
      {
        id: "add",
        label: "Add application",
        group: "Actions",
        hint: "Create",
        keywords: "add new create application",
        run: onAddApplication,
      },
      {
        id: "gmail",
        label: "Import from Gmail",
        group: "Actions",
        hint: "Sync",
        keywords: "gmail import email sync inbox",
        run: onGoToGmail,
      },
      {
        id: "signout",
        label: "Sign out",
        group: "Actions",
        hint: "Account",
        keywords: "sign out logout exit account",
        run: onSignOut,
      },
    ];
    const apps: Command[] = applications.map((a) => ({
      id: `app-${a.id}`,
      label: `${a.company} — ${a.position}`,
      group: "Applications",
      hint: a.status,
      keywords: `${a.company} ${a.position} ${a.status}`,
      run: () => onJumpTo(a.id),
    }));
    return [...actions, ...apps];
  }, [applications, onAddApplication, onGoToGmail, onJumpTo, onSignOut]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter((c) =>
      `${c.label} ${c.keywords}`.toLowerCase().includes(q)
    );
  }, [commands, query]);

  // Reset state and focus the input each time the palette opens.
  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  // Keep the active index valid as the filtered list changes.
  useEffect(() => {
    setActive(0);
  }, [query]);

  // Scroll the highlighted item into view as the user navigates.
  useEffect(() => {
    if (open) {
      document
        .getElementById(`cmdk-opt-${active}`)
        ?.scrollIntoView({ block: "nearest" });
    }
  }, [active, open]);

  if (!open) return null;

  function move(delta: number) {
    setActive((i) =>
      filtered.length === 0 ? 0 : (i + delta + filtered.length) % filtered.length
    );
  }

  function runAndClose(command?: Command) {
    if (!command) return;
    onClose();
    command.run();
  }

  function onInputKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      move(1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      move(-1);
    } else if (e.key === "Enter") {
      e.preventDefault();
      runAndClose(filtered[active]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  }

  return (
    <div className="cmdk-overlay" onMouseDown={onClose}>
      <div
        className="cmdk-panel"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          className="cmdk-input"
          placeholder="Search applications or run a command…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onInputKeyDown}
          role="combobox"
          aria-expanded="true"
          aria-controls="cmdk-list"
          aria-activedescendant={
            filtered[active] ? `cmdk-opt-${active}` : undefined
          }
        />
        <div className="cmdk-list" id="cmdk-list" role="listbox">
          {filtered.length === 0 && (
            <div className="cmdk-empty">No matching commands</div>
          )}
          {filtered.map((command, i) => {
            const newGroup = i === 0 || filtered[i - 1].group !== command.group;
            return (
              <div key={command.id}>
                {newGroup && <div className="cmdk-group">{command.group}</div>}
                <div
                  id={`cmdk-opt-${i}`}
                  role="option"
                  aria-selected={i === active}
                  className={`cmdk-item${i === active ? " is-active" : ""}`}
                  onMouseMove={() => setActive(i)}
                  onClick={() => runAndClose(command)}
                >
                  <span className="cmdk-item-label">{command.label}</span>
                  {command.hint && (
                    <span className="cmdk-item-hint">{command.hint}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        <div className="cmdk-footer">
          <span>
            <kbd>↑</kbd>
            <kbd>↓</kbd> navigate
          </span>
          <span>
            <kbd>↵</kbd> select
          </span>
          <span>
            <kbd>esc</kbd> close
          </span>
        </div>
      </div>
    </div>
  );
}
