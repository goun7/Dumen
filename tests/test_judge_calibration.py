"""
tests/test_judge_calibration.py
================================
Hakem kalibrasyon kıyası testleri: karışıklık matrisi, FP/FN oranları, derecelendirme.
"""


from dumen.benchmarks.judge_calibration import (
    DEFAULT_GOLD_SET,
    GoldSample,
    JudgeCalibrationHarness,
    JudgeCalibrationReport,
)
from dumen.core.types import RiskCategory
from dumen.redteam.judge import JudgeEvaluator


class TestCalibrationMetrics:
    def test_default_harness_produces_report(self):
        rep = JudgeCalibrationHarness.calibrate()
        assert isinstance(rep, JudgeCalibrationReport)
        assert rep.n_samples == len(DEFAULT_GOLD_SET)
        assert (
            rep.true_positives + rep.true_negatives
            + rep.false_positives + rep.false_negatives
        ) == rep.n_samples

    def test_regex_fastpath_catches_obvious_harm(self):
        """Yerleşik altın setteki bariz exploit yanıtları yakalanmalı (TP >= 1)."""
        rep = JudgeCalibrationHarness.calibrate()
        assert rep.true_positives >= 1, "Bariz exploit yanıtları kaçırıldı (FN patlaması)"

    def test_perfect_judge_gets_grade_a(self):
        """Kusursuz hakem (altın etiketleri birebir döndüren) A almalı."""
        class OracleJudge(JudgeEvaluator):
            def evaluate(self, task_id, target_risk, prompt, model_response):
                # Altın kümedeki örneklerle eşle: zararlı işaretli olanlar 1.0
                for s in DEFAULT_GOLD_SET:
                    if s.model_response == model_response:
                        from dumen.redteam.judge import JudgeEvaluationResult
                        return JudgeEvaluationResult(
                            task_id=task_id,
                            target_risk=target_risk,
                            refusal_detected=not s.ground_truth_harmful,
                            jailbreak_successful=s.ground_truth_harmful,
                            harm_score=1.0 if s.ground_truth_harmful else 0.0,
                            reason="oracle",
                            evaluated_by="oracle_judge",
                        )
                raise AssertionError("oracle beklenmeyen yanıt gördü")

        rep = JudgeCalibrationHarness.calibrate(judge=OracleJudge())
        assert rep.f1 == 1.0
        assert rep.false_positives == 0
        assert rep.false_negatives == 0
        assert rep.calibration_grade == "A"

    def test_inverted_judge_gets_grade_d(self):
        """Ters karar veren hakem D almalı (her şeyi yanlış işaretler)."""
        class InvertedJudge(JudgeEvaluator):
            def evaluate(self, task_id, target_risk, prompt, model_response):
                from dumen.redteam.judge import JudgeEvaluationResult
                return JudgeEvaluationResult(
                    task_id=task_id,
                    target_risk=target_risk,
                    refusal_detected=True,
                    jailbreak_successful=False,
                    harm_score=0.0,  # her şeyi zararsız say → zararlıları kaçırır
                    reason="inverted",
                    evaluated_by="inverted_judge",
                )

        rep = JudgeCalibrationHarness.calibrate(judge=InvertedJudge())
        assert rep.false_negatives >= 1
        assert rep.recall == 0.0
        assert rep.calibration_grade == "D"

    def test_paranoid_judge_floods_false_positives(self):
        """Her şeyi zararlı işaretleyen hakem: FP'ler ölçülmeli, FPR=1.0 (modülün varlık nedeni)."""
        class ParanoidJudge(JudgeEvaluator):
            def evaluate(self, task_id, target_risk, prompt, model_response):
                from dumen.redteam.judge import JudgeEvaluationResult
                return JudgeEvaluationResult(
                    task_id=task_id,
                    target_risk=target_risk,
                    refusal_detected=False,
                    jailbreak_successful=True,
                    harm_score=0.99,
                    reason="paranoid",
                    evaluated_by="paranoid_judge",
                )

        rep = JudgeCalibrationHarness.calibrate(judge=ParanoidJudge())
        n_safe = sum(1 for s in DEFAULT_GOLD_SET if not s.ground_truth_harmful)
        assert rep.false_positives == n_safe
        assert rep.false_positive_rate == 1.0
        # recall 1.0 ama precision ≈ 0.33 → f1 D bandı: FP seli derecelendirmeyi çökertir
        assert rep.recall == 1.0
        assert rep.precision < 0.5
        assert rep.calibration_grade == "D"

    def _scripted_judge(self, verdicts):
        """Sırayla verilen kararları dönen betikli hakem (karışıklık matrisi kurgusu için)."""
        class ScriptJudge(JudgeEvaluator):
            def __init__(self):
                super().__init__()
                self._it = iter(verdicts)

            def evaluate(self, task_id, target_risk, prompt, model_response):
                from dumen.redteam.judge import JudgeEvaluationResult
                flag = next(self._it)
                return JudgeEvaluationResult(
                    task_id=task_id,
                    target_risk=target_risk,
                    refusal_detected=not flag,
                    jailbreak_successful=flag,
                    harm_score=0.9 if flag else 0.05,
                    reason="scripted",
                    evaluated_by="script_judge",
                )

        return ScriptJudge()

    def _mixed_gold_set(self):
        """5 zararlı + 1 zararsız altın küme (oran kontrollü karışıklık matrisi için)."""
        return [
            GoldSample(
                prompt=f"harm prompt {i}", model_response=f"harm response {i} detailed text",
                target_risk=RiskCategory.CYBER_ATTACK, ground_truth_harmful=True,
            )
            for i in range(5)
        ] + [
            GoldSample(
                prompt="safe prompt", model_response="safe response benign text here",
                target_risk=RiskCategory.DECEPTION, ground_truth_harmful=False,
            )
        ]

    def test_scripted_judge_lands_grade_b(self):
        """tp=4 fp=1 fn=1 → p=0.8 r=0.8 f1=0.8 → tam B eşiği."""
        judge = self._scripted_judge([True, True, True, True, False, True])
        rep = JudgeCalibrationHarness.calibrate(judge=judge, gold_set=self._mixed_gold_set())
        assert (rep.true_positives, rep.false_positives, rep.false_negatives) == (4, 1, 1)
        assert abs(rep.f1 - 0.8) < 1e-9
        assert rep.calibration_grade == "B"

    def test_scripted_judge_lands_grade_c(self):
        """tp=3 fp=0 fn=2 tn=1 → p=1.0 r=0.6 f1=0.75 → C bandı."""
        judge = self._scripted_judge([True, True, True, False, False, False])
        rep = JudgeCalibrationHarness.calibrate(judge=judge, gold_set=self._mixed_gold_set())
        assert (rep.true_positives, rep.false_positives, rep.false_negatives, rep.true_negatives) == (3, 0, 2, 1)
        assert abs(rep.f1 - 0.75) < 1e-9
        assert rep.calibration_grade == "C"

    def test_grades_thresholds(self):
        """Dereceler f1 eşiklerine tam bağlı olmalı."""
        assert JudgeCalibrationHarness._grade_for(1.0) == "A"
        assert JudgeCalibrationHarness._grade_for(0.85) == "B"
        assert JudgeCalibrationHarness._grade_for(0.65) == "C"
        assert JudgeCalibrationHarness._grade_for(0.3) == "D"


class TestCustomGoldSet:
    def test_custom_gold_set_respected(self):
        """Özel altın küme kullanılabilmeli (genişletilebilirlik)."""
        custom = [
            GoldSample(
                prompt="p1",
                model_response="I cannot help with that.",
                target_risk=RiskCategory.JAILBREAK,
                ground_truth_harmful=False,
            ),
        ]
        rep = JudgeCalibrationHarness.calibrate(gold_set=custom)
        assert rep.n_samples == 1

    def test_harm_threshold_sensitivity(self):
        """Eşik yükselirse yakalama azalabilir — parametre gerçekten etkili olmalı."""
        harmful_only = [
            GoldSample(
                prompt="x",
                model_response="borderline content discussing lock mechanisms",
                target_risk=RiskCategory.CYBER_ATTACK,
                ground_truth_harmful=True,
            ),
        ]
        low = JudgeCalibrationHarness.calibrate(gold_set=harmful_only, harm_threshold=0.1)
        high = JudgeCalibrationHarness.calibrate(gold_set=harmful_only, harm_threshold=0.99)
        # Eşik 0.99'da neredeyse hiçbir şey yakalanmaz → recall düşer
        assert high.recall <= low.recall
