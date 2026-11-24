"""Context indexer path-boundary and secret-exclusion tests."""

from personal_ai_api import cli


def test_index_path_skips_symlink_to_outside_approved_root(tmp_path, monkeypatch):
    approved = tmp_path / "approved"
    outside = tmp_path / "private"
    approved.mkdir()
    outside.mkdir()
    secret = outside / "private_notes.txt"
    secret.write_text("this must not be indexed", encoding="utf-8")
    (approved / "readme.md").write_text("safe documentation", encoding="utf-8")
    (approved / "linked.txt").symlink_to(secret)

    monkeypatch.setenv("PAI_CONTEXT_INDEX_ROOTS", str(approved))
    indexed = []
    monkeypatch.setattr(
        cli,
        "_index_document",
        lambda title, body, source: indexed.append((title, body, source)) or "doc-test",
    )

    result = cli._index_path(str(approved))
    assert result == {"indexed": 1, "skipped": 1, "failed": 0}
    assert [item[1] for item in indexed] == ["safe documentation"]


def test_index_path_rejects_symlink_as_requested_target(tmp_path, monkeypatch):
    approved = tmp_path / "approved"
    outside = tmp_path / "outside"
    approved.mkdir()
    outside.mkdir()
    secret = outside / "private.txt"
    secret.write_text("private", encoding="utf-8")
    link = approved / "shortcut.txt"
    link.symlink_to(secret)
    monkeypatch.setenv("PAI_CONTEXT_INDEX_ROOTS", str(approved))

    try:
        cli._index_path(str(link))
    except SystemExit as exc:
        assert "symlink" in str(exc).lower()
    else:
        raise AssertionError("symlink target must be rejected")
