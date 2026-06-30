"""Rule-based classifier that tags emails as job-related and infers status.

This is intentionally simple and deterministic (keyword + sender rules) so it is
easy to test and reason about. Stage 3 will use these tags to create/update
Application records.
"""

import re
from email.utils import parseaddr

# Applicant-tracking-system domains. Mail from these is almost always job-related.
ATS_DOMAINS = {
    "greenhouse.io",
    "us.greenhouse-mail.io",
    "lever.co",
    "hire.lever.co",
    "myworkday.com",
    "ashbyhq.com",
    "smartrecruiters.com",
    "icims.com",
    "taleo.net",
    "jobvite.com",
    "workable.com",
    "breezy.hr",
    "bamboohr.com",
    "rippling-mail.com",
    "gem.com",
}

# Status keyword sets. Order of evaluation (in classify) sets precedence.
REJECTED_KEYWORDS = (
    "unfortunately",
    "we regret",
    "regret to inform",
    "not moving forward",
    "not be moving forward",
    "will not be proceeding",
    "decided not to proceed",
    "decided to move forward with other",
    "other candidates",
    "no longer under consideration",
    "not selected",
    "won't be moving forward",
    "we have decided",
    "wish you the best",
)

OFFER_KEYWORDS = (
    "offer letter",
    "pleased to offer",
    "excited to offer",
    "extend an offer",
    "job offer",
    "your offer",
)

INTERVIEW_KEYWORDS = (
    "interview",
    "phone screen",
    "technical screen",
    "schedule a call",
    "schedule some time",
    "set up a call",
    "next steps",
    "availability",
    "would love to chat",
    "speak with you",
    "meet with",
    "coding challenge",
    "online assessment",
    "take-home",
    "hackerrank",
    "codesignal",
)

APPLIED_KEYWORDS = (
    "application received",
    "we received your application",
    "thank you for applying",
    "thanks for applying",
    "application submitted",
    "successfully applied",
    "received your application",
    "your application for",
    "application has been received",
)

# Generic signals that an email is job-related even without a status match.
JOB_RELATED_KEYWORDS = (
    "application",
    "applied",
    "recruiter",
    "recruiting",
    "talent acquisition",
    "hiring",
    "position",
    "the role",
    "your candidacy",
    "job",
    "career",
    "interview",
)

# Words stripped from sender display names when guessing a company.
_NAME_NOISE = re.compile(
    r"\b(via|recruiting|recruitment|talent(?:\s+acquisition)?|careers?|team|"
    r"hr|people\s+ops|no[-\s]?reply|do[-\s]?not[-\s]?reply|notifications?|"
    r"jobs?|hiring|the)\b",
    re.IGNORECASE,
)

# Public mailbox providers: never use these as a company guess.
_PUBLIC_PROVIDERS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "live.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
}


def _domain(sender: str) -> str:
    """Return the lowercased domain part of a From header, or ''."""
    _, addr = parseaddr(sender)
    if "@" not in addr:
        return ""
    return addr.rsplit("@", 1)[-1].lower().strip()


def _is_ats(domain: str) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in ATS_DOMAINS)


def _contains_any(text: str, keywords) -> bool:
    return any(k in text for k in keywords)


def _company_from_sender(sender: str) -> str | None:
    """Best-effort company name from a From header's display name or domain."""
    name, addr = parseaddr(sender)

    if name:
        cleaned = _NAME_NOISE.sub("", name)
        cleaned = re.sub(r"[\s\-|,]+", " ", cleaned).strip()
        # Drop a trailing email-looking remnant.
        cleaned = re.sub(r"\S+@\S+", "", cleaned).strip()
        if len(cleaned) >= 2:
            return cleaned

    domain = _domain(sender)
    if not domain or domain in _PUBLIC_PROVIDERS or _is_ats(domain):
        return None
    # Second-level label, e.g. "jobs.stripe.com" -> "Stripe".
    parts = domain.split(".")
    if len(parts) >= 2:
        label = parts[-2]
        return label.capitalize()
    return None


def detect_status(text: str) -> str | None:
    """Infer an application status from email text, or None if unclear."""
    if _contains_any(text, REJECTED_KEYWORDS):
        return "rejected"
    if _contains_any(text, OFFER_KEYWORDS):
        return "offer"
    if _contains_any(text, INTERVIEW_KEYWORDS):
        return "interview"
    if _contains_any(text, APPLIED_KEYWORDS):
        return "applied"
    return None


def classify(subject: str, sender: str, snippet: str = "") -> dict:
    """Classify one email.

    Returns a dict with:
      - is_job_related: bool
      - detected_status: one of applied/interview/offer/rejected, or None
      - company_guess: best-effort company name, or None
    """
    text = f"{subject or ''} {snippet or ''}".lower()
    domain = _domain(sender)
    from_ats = _is_ats(domain)

    status = detect_status(text)
    is_job_related = from_ats or status is not None or _contains_any(
        text, JOB_RELATED_KEYWORDS
    )

    company = _company_from_sender(sender) if is_job_related else None

    return {
        "is_job_related": is_job_related,
        "detected_status": status,
        "company_guess": company,
    }
