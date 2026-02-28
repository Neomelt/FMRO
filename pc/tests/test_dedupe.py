from fmro_pc.crawl.dedupe import build_fingerprint


def test_fingerprint_is_stable_with_whitespace_and_case() -> None:
    first = build_fingerprint(
        company_name="  ACME  ",
        title=" Robotics Intern ",
        apply_url="HTTPS://example.com/jobs/123 ",
        location="Shanghai",
        source_url="https://example.com/source",
    )
    second = build_fingerprint(
        company_name="acme",
        title="robotics intern",
        apply_url="https://example.com/jobs/123",
        location="shanghai",
        source_url="https://example.com/source",
    )

    assert first == second


def test_fingerprint_falls_back_when_apply_url_missing() -> None:
    with_apply = build_fingerprint(
        company_name="ACME",
        title="ML Engineer",
        apply_url="https://acme.example/jobs/1",
        location="Beijing",
        source_url="https://acme.example/careers",
    )
    no_apply = build_fingerprint(
        company_name="ACME",
        title="ML Engineer",
        apply_url=None,
        location="Beijing",
        source_url="https://acme.example/careers",
    )
    no_apply_duplicate = build_fingerprint(
        company_name="acme",
        title="ml engineer",
        apply_url="",
        location="beijing",
        source_url="https://acme.example/careers",
    )

    assert with_apply != no_apply
    assert no_apply == no_apply_duplicate
