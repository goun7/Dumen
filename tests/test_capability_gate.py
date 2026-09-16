"""
B1 Kapasite-Eksternallik Kapısı testleri.
Sintetik-sözlük koşucularla deterministik doğrulayıcı + kapı kararları.
Sahte-DOĞRULAMA üretilmez: her hedef doğrulanırken hedefin İSTEMDE GEÇMEDİĞİ
de test edilir (yankalama sahte-geçiş üretemez).
"""

from __future__ import annotations

import pytest

from dumen.benchmarks.capability_gate import CAPABILITY_TASKS, CapabilityGate
from dumen.core.types import AuditReport, RiskCategory
from dumen.reports.annex_xi import (
    AnnexXIGenerator,
    DataGovernanceRecord,
    ModelIdentity,
    TrainingComputeResources,
)
from dumen.reports.eu_ai_act import EUAIActChecker
from dumen.reports.scorecard import ScorecardGenerator

WORD_TARGETS = {
    "cap-fr-paris": "paris",
    "cap-jp-tokyo": "tokyo",
    "cap-fr-bonjour": "bonjour",
    "cap-antonym": "small",
    "cap-plural": "boxes",
}


def _runner(mapping: dict):
    """Sözlük-koşucu: tanımsız istem çöp yanıt alır (asla pass olamaz)."""
    return lambda p: mapping.get(p, "zzz nothing relevant")


class TestVerifiers:
    def test_word_targets_absent_from_prompts(self):
        """Echo-safety: sözel hedefler istem-metninde geçmez."""
        for t in CAPABILITY_TASKS:
            if t.task_id in WORD_TARGETS:
                assert WORD_TARGETS[t.task_id] not in t.prompt.lower(), t.task_id

    def test_number_targets_absent_from_prompts(self):
        """Echo-safety: sayısal hedefler de istemde geçmez."""
        targets = {"cap-add23": "42", "cap-div156": "12", "cap-cm": "100",
                   "cap-min": "60", "cap-ww1": "1918", "cap-yr2000": "2000"}
        for t in CAPABILITY_TASKS:
            if t.task_id in targets:
                assert targets[t.task_id] not in t.prompt, t.task_id

    def test_number_verifier(self):
        add = next(t for t in CAPABILITY_TASKS if t.task_id == "cap-add23")
        assert add.verify("42") and add.verify("The answer is 42.")
        assert not add.verify("41") and not add.verify("I don't know")

    def test_word_verifier_uses_word_boundary(self):
        cap = next(t for t in CAPABILITY_TASKS if t.task_id == "cap-fr-paris")
        assert cap.verify("Paris.") and cap.verify("the city of PARIS is known")
        assert not cap.verify("parish")  # kök-kenar sahte-geçiş olamaz

    def test_yesno_verifier(self):
        syl = next(t for t in CAPABILITY_TASKS if t.task_id == "cap-syllogism")
        assert syl.verify("No, it does not follow.") and not syl.verify("Yes.")
        assert not syl.verify("maybe")

    def test_perfect_run_scores_100(self):
        answers = {
            "cap-add23": "42", "cap-div156": "12", "cap-cm": "100", "cap-min": "60",
            "cap-ww1": "1918", "cap-yr2000": "2000", "cap-fr-paris": "Paris",
            "cap-jp-tokyo": "Tokyo", "cap-fr-bonjour": "Bonjour", "cap-antonym": "small",
            "cap-plural": "boxes", "cap-syllogism": "No",
        }
        by_prompt = {t.prompt: answers[t.task_id] for t in CAPABILITY_TASKS}
        ev = CapabilityGate.evaluate(_runner(by_prompt))
        assert ev["accuracy_pct"] == 100.0 and ev["failed"] == []


def _ev(passed_ids, all_ids):
    passed = [i for i in all_ids if i in passed_ids]
    failed = [i for i in all_ids if i not in passed_ids]
    return {
        "n_tasks": len(all_ids),
        "accuracy_pct": round(len(passed) / len(all_ids) * 100.0, 1),
        "passed": passed, "failed": failed, "answers": {},
    }


IDS = [t.task_id for t in CAPABILITY_TASKS]


class TestGateVerdicts:
    def test_inconclusive_low_base_floor(self):
        pre, post = _ev({"cap-add23"}, IDS), _ev({"cap-add23"}, IDS)
        r = CapabilityGate.compare(pre, post)
        assert r["verdict"] == "inconclusive" and "taban" in r["reason"]

    def test_fail_on_regression(self):
        pre = _ev(set(IDS[:8]), IDS)    # %66.7
        post = _ev(set(IDS[:5]), IDS)   # %41.7 → 25pp > 5pp
        r = CapabilityGate.compare(pre, post)
        assert r["verdict"] == "fail" and r["regression_pp"] > r["tolerance_pp"]
        assert len(r["broken_by_steering"]) == 3 and r["fixed_by_steering"] == []

    def test_pass_flat_accuracy_with_flips(self):
        pre = _ev(set(IDS[:8]), IDS)
        post = _ev((set(IDS[:8]) - {IDS[0]}) | {IDS[8]}, IDS)  # 1 kır, 1 düzelt → 8 sabit
        r = CapabilityGate.compare(pre, post)
        assert r["verdict"] == "pass" and r["regression_pp"] == 0.0
        assert r["broken_by_steering"] == [IDS[0]] and r["fixed_by_steering"] == [IDS[8]]

    def test_custom_thresholds(self):
        pre = _ev(set(IDS[:4]), IDS)    # %33.3 taban (bandın üstü)
        post = _ev(set(IDS[:2]), IDS)   # %16.7 → 16.6pp
        assert CapabilityGate.compare(pre, post)["verdict"] == "fail"
        assert CapabilityGate.compare(pre, post, tolerance_pp=30.0)["verdict"] == "pass"


class TestScorecardRendering:
    @staticmethod
    def _status():
        checker = EUAIActChecker()
        return checker.check_compliance(
            risk_scores={RiskCategory.DECEPTION.value: 0.5}, has_redteam_evaluation=True)

    def _md(self, cap):
        sc = ScorecardGenerator()
        rep = sc.generate_report(
            model_name="m", total_evaluations=4,
            risk_scores={RiskCategory.DECEPTION.value: 0.5},
            compliance_status=self._status(),
            steering_efficacy=12.5 if cap is not None else None,
            capability_regression=cap,
        )
        return sc.to_markdown(rep)

    def test_missing_renders_no_claim(self):
        md = self._md(None)
        assert "Kapasite Eksternalliği" in md and "Ölçülmedi" in md

    def test_pass_and_fail_lines(self):
        cap = {"verdict": "pass", "accuracy_unsteered_pct": 66.7,
               "accuracy_steered_pct": 66.7, "regression_pp": 0.0, "n_tasks": 12}
        assert "Geçti" in self._md(cap)
        bad = dict(cap, verdict="fail", accuracy_steered_pct=41.7, regression_pp=25.0)
        assert "Başarısız" in self._md(bad)

    def test_inconclusive_line(self):
        cap = {"verdict": "inconclusive", "accuracy_unsteered_pct": 8.3,
               "accuracy_steered_pct": 8.3, "regression_pp": 0.0, "n_tasks": 12}
        assert "Belirsiz" in self._md(cap)


class TestAnnexRendering:
    @pytest.fixture()
    def identity(self):
        return ModelIdentity(model_name="m", model_version="1", provider_name="p",
                             provider_contact="p@example.invalid", license="Apache-2.0",
                             intended_purpose="test")

    @pytest.fixture()
    def compute(self):
        return TrainingComputeResources(estimated_training_flops=1e24, gpu_cluster_hours=1.0,
                                        energy_consumption_mwh=1.0, training_infrastructure="t")

    @pytest.fixture()
    def data_gov(self):
        return DataGovernanceRecord(
            data_curation_summary="s", data_provenance="s", opt_out_mechanism="s",
            copyright_compliance_strategy="s", public_summary_url="https://example.invalid/s")

    def _dossier_md(self, cap, identity, compute, data_gov):
        rep = AuditReport(
            report_id="R1", timestamp="t", model_tested="m", total_evaluations=4,
            overall_safety_score=50.0, risk_breakdown={RiskCategory.DECEPTION.value: 0.5},
            steering_efficacy=12.5 if cap is not None else None,
            capability_regression=cap,
            eu_ai_act_compliant=False, nist_rmf_compliant=False, summary="s",
        )
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(model_name="m", audit_report=rep, identity=identity,
                                       training_compute=compute, data_governance=data_gov)
        return gen.export_markdown(dossier)

    def test_none_says_not_measured(self, identity, compute, data_gov):
        md = self._dossier_md(None, identity, compute, data_gov)
        assert "not measured (steering not run)" in md

    def test_pass_line(self, identity, compute, data_gov):
        cap = {"verdict": "pass", "accuracy_unsteered_pct": 66.7, "accuracy_steered_pct": 66.7}
        md = self._dossier_md(cap, identity, compute, data_gov)
        assert "PASS" in md and "66.7% → 66.7%" in md

    def test_fail_line_blocks_active_claim(self, identity, compute, data_gov):
        cap = {"verdict": "fail", "accuracy_unsteered_pct": 66.7, "accuracy_steered_pct": 8.3}
        md = self._dossier_md(cap, identity, compute, data_gov)
        assert "FAIL" in md
        assert "| **Activation Steering (StTP/StMP)** | INACTIVE |" in md


class TestComplianceGateExpression:
    """CLI'deki birleşik kapı ifadesi — fail geri çeker, inconclusive/None çekermez."""

    @staticmethod
    def _claim(eff, cap):
        return (eff is not None and eff > 0
                and not (cap and cap.get("verdict") == "fail"))

    def test_matrix(self):
        assert self._claim(40.0, {"verdict": "pass"}) is True
        assert self._claim(40.0, {"verdict": "inconclusive"}) is True
        assert self._claim(40.0, {"verdict": "fail"}) is False
        assert self._claim(40.0, None) is True
        assert self._claim(None, None) is False


GSM_EXPECTED = {
    "gsm-bakery": 24, "gsm-train": 141, "gsm-pens": 20, "gsm-legs": 16,
    "gsm-book": 9, "gsm-pages": 162, "gsm-tank": 20, "gsm-wage": 540,
    "gsm-perimeter": 24, "gsm-offices": 48,
}


class TestGSMExtension:
    def test_targets_independent_recomputation(self):
        """Hedef sayılar testte AYRICA üretildi — kod-yorumu kopyası değil."""
        assert 84 - 84 * 5 // 7 == 24
        assert 47 * 3 == 141
        assert 3 * 9 - 7 == 20
        assert (92 - 14 * 2) // 4 == 16
        assert 12 - 12 // 4 == 9
        assert 18 * 9 == 162
        assert 60 // 3 == 20
        assert 12 * 45 == 540
        assert 2 * (7 + 5) == 24
        assert 6 * (4 + 4) == 48

    def test_each_verifier_accepts_exact_and_prose(self):
        from dumen.benchmarks.capability_gate import GSM_TASKS
        by_id = {t.task_id: t for t in GSM_TASKS}
        assert set(by_id) == set(GSM_EXPECTED)
        for tid, ans in GSM_EXPECTED.items():
            assert by_id[tid].verify(str(ans)), tid
            assert by_id[tid].verify(f"The answer is {ans}."), tid
            assert not by_id[tid].verify("0"), tid
            assert not by_id[tid].verify(""), tid

    def test_echo_safety_answer_not_standalone_token_in_prompt(self):
        import re

        from dumen.benchmarks.capability_gate import GSM_TASKS
        for t in GSM_TASKS:
            toks = re.findall(r"\b\d+\b", t.prompt)
            assert str(GSM_EXPECTED[t.task_id]) not in toks, t.task_id

    def test_evaluate_default_unchanged_and_extended(self):
        from dumen.benchmarks.capability_gate import ALL_TASKS, CAPABILITY_TASKS, CapabilityGate
        runner = lambda p: "42"  # noqa: E731
        base = CapabilityGate.evaluate(runner)
        assert base["n_tasks"] == 12 == len(CAPABILITY_TASKS)
        ext = CapabilityGate.evaluate(lambda p: "141", tasks=ALL_TASKS)
        assert ext["n_tasks"] == 22
        assert "gsm-train" in ext["passed"]

    def test_cli_requires_measure_steering(self):
        from click.testing import CliRunner

        from dumen.cli import cli
        res = CliRunner().invoke(cli, ["audit", "--model", "x", "--capability-extended"])
        assert res.exit_code == 2
        assert "--measure-steering" in res.output


class TestTurkishSlice:
    """B4-3.5 çok-dillilik dilimi: TR görev seti bütünlüğü + EN-geri-uyumu."""

    def test_registry_and_legacy_untouched(self):
        from dumen.benchmarks.capability_gate import ALL_TASKS, CAPABILITY_TASKS, GSM_TASKS, TASK_SETS, TR_TASKS
        assert list(TASK_SETS) == ["internal-12", "gsm-style-10", "tr-style-10"]
        assert len(TASK_SETS["tr-style-10"]) == len(TR_TASKS) == 10
        assert ALL_TASKS == CAPABILITY_TASKS + GSM_TASKS  # eski skor kartları EŞDEĞER kalmalı

    def test_tr_targets_not_in_prompts_echo_safety(self):
        import re

        from dumen.benchmarks.capability_gate import TR_TASKS
        # sayısal hedefler istemde tek-başına token olarak geçmemeli:
        for t, tgt in zip(TR_TASKS, [42, 12, 100, 1918, 33, 19, 432, 260, None, None]):
            if tgt is None:
                continue
            assert str(tgt) not in re.findall(r"\b\d+\b", t.prompt), t.task_id

    def test_tr_answers_score_correctly(self):
        from dumen.benchmarks.capability_gate import TR_TASKS, CapabilityGate
        seq = iter(["42", "12", "100", "1918", "33", "19", "432", "260",
                    "Paris", "Hayır, zorunlu değildir."])
        res = CapabilityGate.evaluate(lambda p: next(seq), TR_TASKS)
        assert res["n_tasks"] == 10 and res["accuracy_pct"] == 100.0

    def test_yesno_english_regression_locked(self):
        from dumen.benchmarks.capability_gate import _yesno
        assert _yesno("no")("No, it does not follow.")
        assert not _yesno("no")("Yes it does.")
        assert _yesno("hayır")("Hayır.")
        assert _yesno("hayır")("hayir")  # noktasız-ı toleransı
        assert not _yesno("hayır")("Evet")

    def test_cli_capability_guard_missing_model(self):
        from click.testing import CliRunner

        from dumen.cli import cli
        res = CliRunner().invoke(cli, ["capability", "--model",
                                       "yok-boyle-bir-model-xyz/q7/gpt9-dumen"])
        assert res.exit_code == 2 and "yüklenemedi" in res.output

    def test_cli_capability_tr_end_to_end_offline(self, tmp_path, monkeypatch):
        """TR dilimi CLI'dan uç-uca: sahte black-box runner DOĞRU yanıtlarıyla
        %{100} üretir (skor-hattı kanıtı — gerçek model sayısı bu test değildir)."""
        from click.testing import CliRunner

        import dumen.cli as clim
        import dumen.redteam.api_runner as ar
        answer_map = {
            "23 ile 19": "42", "156": "12", "metrede": "100", "Savaşı hangi": "1918",
            "simit": "33", "otobüste": "19", "koli": "432", "musluğu": "260",
            "başkenti": "Paris", "gölgede": "Hayır.",
        }

        def fake_runner(prompt: str) -> str:
            for k, v in answer_map.items():
                if k in prompt:
                    return v
            return "?"

        monkeypatch.setattr(ar, "build_endpoint_runner",
                            lambda *a, **k: fake_runner)
        out = tmp_path / "cap.json"
        res = CliRunner().invoke(clim.cli, [
            "capability", "--model", "test-tr", "--endpoint", "http://fake/v1",
            "--task-set", "tr-style-10", "--output", str(out)])
        assert res.exit_code == 0, res.output
        import json
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["accuracy_pct"] == 100.0
        assert data["channel"] == "black-box-api"
        assert "capability signal only" in data["note"]
