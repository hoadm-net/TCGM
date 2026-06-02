import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tcgm.evaluation.answer_metrics import LongMemEvalAnswerEvaluator
from tcgm.evaluation.aggregates import QuestionMetricRecord, aggregate_question_metrics
from tcgm.evaluation.lafs import FIXED_FRONTIER_POINTS, Point, lafs_gain_for_submission
from tcgm.evaluation.retrieval_metrics import mean_reciprocal_rank, precision_recall_f1


class EvaluationMetricsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        questions_path = Path("/home/hoadm/TCGM/datasets/LongMemEval-V2/data/longmemeval-v2/questions.jsonl")
        cls.questions = []
        with questions_path.open() as handle:
            for index, line in enumerate(handle):
                if index >= 6:
                    break
                cls.questions.append(json.loads(line))

    def test_lmev2_answer_evaluator_matches_gold_examples(self):
        evaluator = LongMemEvalAnswerEvaluator()
        predictions = [
            "\\boxed{Incident Mobile, Incident Portal, My Open Incidents}",
            "\\boxed{Reports;Problems}",
            "\\boxed{300}",
            "\\boxed{That scheduling workflow does not use a second duration-deciding field besides risk level.}",
            "\\boxed{G}",
            "\\boxed{100}",
        ]
        for question, prediction in zip(self.questions, predictions):
            score = evaluator.evaluate(question_item=question, prediction=prediction)
            self.assertTrue(score.correct, question["id"])

    def test_overlap_and_ranking_metrics(self):
        overlap = precision_recall_f1(["a", "b", "c"], ["b", "c", "d"])
        self.assertAlmostEqual(overlap.precision, 2 / 3)
        self.assertAlmostEqual(overlap.recall, 2 / 3)
        self.assertAlmostEqual(mean_reciprocal_rank(["x", "y", "gold"], ["gold"]), 1 / 3)

    def test_aggregate_metrics(self):
        evaluator = LongMemEvalAnswerEvaluator()
        score_static = evaluator.evaluate(question_item=self.questions[0], prediction="\\boxed{Incident Mobile, Incident Portal, My Open Incidents}")
        score_abs = evaluator.evaluate(question_item=self.questions[3], prediction="\\boxed{That scheduling workflow does not use a second duration-deciding field besides risk level.}")
        score_mc = evaluator.evaluate(question_item=self.questions[4], prediction="\\boxed{G}")
        rows = [
            QuestionMetricRecord(
                question_id=self.questions[0]["id"],
                question_type=self.questions[0]["question_type"],
                answer_score=score_static,
                latency_seconds=2.0,
                retrieval_latency_seconds=0.4,
                gold_seed_ids=("n1", "n2"),
                predicted_seed_ids=("n2",),
                gold_subgraph_ids=("n1", "n2", "n3"),
                predicted_subgraph_ids=("n2", "n3"),
                gold_evidence_ids=("n2", "n3"),
                predicted_evidence_ids=("n3",),
                nodes_visited=12,
                hops_expanded=2,
                prompt_tokens=100,
                completion_tokens=20,
                total_tokens=120,
            ),
            QuestionMetricRecord(
                question_id=self.questions[3]["id"],
                question_type=self.questions[3]["question_type"],
                answer_score=score_abs,
                latency_seconds=3.0,
                retrieval_latency_seconds=0.8,
                gold_evidence_ids=("n4",),
                predicted_evidence_ids=("n4",),
                nodes_visited=20,
                hops_expanded=3,
                prompt_tokens=200,
                completion_tokens=30,
                total_tokens=230,
                memory_context_original_tokens=1000,
                memory_context_final_tokens=600,
                memory_context_truncated=True,
            ),
            QuestionMetricRecord(
                question_id=self.questions[4]["id"],
                question_type=self.questions[4]["question_type"],
                answer_score=score_mc,
                latency_seconds=1.5,
                retrieval_latency_seconds=0.2,
                gold_evidence_ids=("n7",),
                predicted_evidence_ids=("n8",),
                nodes_visited=7,
                hops_expanded=1,
                prompt_tokens=50,
                completion_tokens=10,
                total_tokens=60,
            ),
        ]
        aggregated = aggregate_question_metrics(rows)
        self.assertEqual(aggregated["overall"]["count_all_questions"], 3)
        self.assertAlmostEqual(aggregated["overall"]["overall_full_set"], 1.0)
        self.assertAlmostEqual(aggregated["memory_query"]["avg_seconds"], (0.4 + 0.8 + 0.2) / 3)
        self.assertEqual(aggregated["metric_coverage"]["heuristic_llm_questions"], 1)

    def test_lafs_gain(self):
        gain = lafs_gain_for_submission(
            FIXED_FRONTIER_POINTS["small"],
            [Point("Fast symbolic TCGM", acc=62.0, latency=15.0)],
        )
        self.assertGreater(gain, 0.0)
        dominated_gain = lafs_gain_for_submission(
            FIXED_FRONTIER_POINTS["small"],
            [Point("Dominated point", acc=60.0, latency=150.0)],
        )
        self.assertAlmostEqual(dominated_gain, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()