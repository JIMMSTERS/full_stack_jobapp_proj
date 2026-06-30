"""Tests for the rule-based email classifier."""

from app import classifier


def test_application_received_is_applied():
    result = classifier.classify(
        subject="Thank you for applying to Stripe",
        sender="Stripe Recruiting <no-reply@greenhouse.io>",
        snippet="We have received your application for the Backend Engineer role.",
    )
    assert result["is_job_related"] is True
    assert result["detected_status"] == "applied"
    assert result["company_guess"] == "Stripe"


def test_interview_invitation():
    result = classifier.classify(
        subject="Next steps: interview with Datadog",
        sender="Jane from Datadog <jane@datadog.com>",
        snippet="We'd love to schedule a call to discuss the role. What's your availability?",
    )
    assert result["is_job_related"] is True
    assert result["detected_status"] == "interview"


def test_offer_email():
    result = classifier.classify(
        subject="Your offer from Notion",
        sender="recruiting@notion.so",
        snippet="We are pleased to offer you the position. Offer letter attached.",
    )
    assert result["detected_status"] == "offer"


def test_rejection_takes_precedence_over_interview():
    result = classifier.classify(
        subject="Update on your application",
        sender="careers@airbnb.com",
        snippet="After your interview, unfortunately we will not be moving forward.",
    )
    assert result["detected_status"] == "rejected"


def test_non_job_email_is_not_job_related():
    result = classifier.classify(
        subject="Your Amazon order has shipped",
        sender="ship-confirm@amazon.com",
        snippet="Your package is on the way.",
    )
    assert result["is_job_related"] is False
    assert result["detected_status"] is None
    assert result["company_guess"] is None


def test_ats_sender_is_job_related_without_keywords():
    result = classifier.classify(
        subject="A message about your candidacy",
        sender="Lever <no-reply@hire.lever.co>",
        snippet="Tap to view the latest update.",
    )
    assert result["is_job_related"] is True


def test_company_guess_ignores_public_provider():
    result = classifier.classify(
        subject="Following up on the position",
        sender="John Smith <john.smith@gmail.com>",
        snippet="Are you still interested in the role?",
    )
    # Job-related via keywords, but no company should be guessed from gmail.com.
    assert result["is_job_related"] is True
    assert result["company_guess"] == "John Smith"


def test_company_guess_from_domain_when_no_display_name():
    result = classifier.classify(
        subject="Your application for Software Engineer",
        sender="jobs@stripe.com",
        snippet="Thanks for applying.",
    )
    assert result["company_guess"] == "Stripe"
