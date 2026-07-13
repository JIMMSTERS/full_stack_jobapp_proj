"""Turn classified Gmail messages into tracked Application records.

The grouping logic (``summarize_threads``) is pure and easily tested. The
``import_messages`` function applies those summaries to the database, creating
new applications and updating existing ones (deduped by Gmail thread).
"""

from sqlalchemy.orm import Session

from app import classifier, crud, gmail, llm, models

DEFAULT_POSITION = "Unknown role"


def _latest_first(messages: list[dict]) -> list[dict]:
    """Sort a thread's messages newest-first by Gmail internal date."""
    return sorted(messages, key=lambda m: m.get("internal_date", 0), reverse=True)


def summarize_threads(messages: list[dict]) -> list[dict]:
    """Group job-related messages by thread into one summary each.

    Each summary reflects the *latest* email in the thread, since the most
    recent message best represents the application's current state. Messages
    that aren't job-related, or have no guessable company, are ignored.

    Returns a list of dicts: {thread_id, company, position, status}.
    """
    threads: dict[str, list[dict]] = {}
    for message in messages:
        result = llm.smart_classify(
            subject=message.get("subject", ""),
            sender=message.get("from", ""),
            snippet=message.get("snippet", ""),
        )
        if not result["is_job_related"] or not result["company_guess"]:
            continue
        enriched = {**message, "_classification": result}
        thread_id = message.get("thread_id") or message.get("id")
        threads.setdefault(thread_id, []).append(enriched)

    summaries: list[dict] = []
    for thread_id, thread_messages in threads.items():
        ordered = _latest_first(thread_messages)

        company = next(
            (m["_classification"]["company_guess"] for m in ordered
             if m["_classification"]["company_guess"]),
            None,
        )
        status = next(
            (m["_classification"]["detected_status"] for m in ordered
             if m["_classification"]["detected_status"]),
            "applied",
        )
        position = None
        for m in ordered:
            position = classifier.guess_position(
                m.get("subject", ""), m.get("snippet", "")
            )
            if position:
                break

        summaries.append(
            {
                "thread_id": thread_id,
                "company": company,
                "position": position or DEFAULT_POSITION,
                "status": status,
            }
        )

    return summaries


def import_messages(
    db: Session, user_id: int, messages: list[dict]
) -> dict:
    """Create/update applications from already-fetched Gmail messages.

    Returns {created, updated, unchanged} counts.
    """
    created = updated = unchanged = 0

    for summary in summarize_threads(messages):
        existing = crud.get_application_by_thread(
            db, user_id, summary["thread_id"]
        )
        if existing is None:
            crud.create_imported_application(
                db,
                user_id=user_id,
                company=summary["company"],
                position=summary["position"],
                status=summary["status"],
                gmail_thread_id=summary["thread_id"],
            )
            created += 1
            continue

        changed = False
        if existing.status != summary["status"]:
            existing.status = summary["status"]
            changed = True
        if existing.position in ("", DEFAULT_POSITION) and summary[
            "position"
        ] not in ("", DEFAULT_POSITION):
            existing.position = summary["position"]
            changed = True
        if not existing.company and summary["company"]:
            existing.company = summary["company"]
            changed = True

        if changed:
            db.commit()
            updated += 1
        else:
            unchanged += 1

    return {"created": created, "updated": updated, "unchanged": unchanged}


def import_from_gmail(
    db: Session, user: models.User, max_results: int = 25
) -> dict:
    """Fetch recent Gmail messages and import them into applications."""
    messages = gmail.list_recent_messages(db, user, max_results=max_results)
    return import_messages(db, user.id, messages)
