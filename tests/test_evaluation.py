from app import evaluation


def test_offline_retrieval_meets_quality_gate():
    report = evaluation.evaluate()
    assert report["passed"], report
    assert report["case_count"] == 10
    assert len(report["cases"]) == 10


def test_quality_gate_fails_when_retrieval_loses_all_hits(monkeypatch, capsys):
    monkeypatch.setattr(evaluation, "_search_repository", lambda *args: [])
    assert evaluation.main() == 1
    assert '"passed": false' in capsys.readouterr().out
