import pytest

from src.constants import SUBJECTS
from src.optimization import optimization


@pytest.fixture
def standard_scores():
    return {
        subject: [400.0 + 10.0 * hits for hits in range(1, 16)]
        for subject in SUBJECTS
    }


@pytest.fixture(autouse=True)
def course_weights(monkeypatch):
    monkeypatch.setattr(
        "src.optimization.utils.readCourseWeights",
        lambda course: {subject: 1 for subject in SUBJECTS},
    )


def test_essay_is_optimized_independently(standard_scores):
    result = optimization(
        course="Curso de teste",
        min_AC=100.0,
        std_scores=standard_scores,
        constraints_dict={},
        min_subjects=[],
        essay_options=[
            {"raw_score": 4.5, "standard_score": 250.0},
            {"raw_score": 4.6, "standard_score": 255.0},
        ],
        port_red_objective="essay",
    )

    assert result.solve_status == "Optimal"
    assert result.chosen_hits["PORT_RED"]["essay_score"] == 4.5
    assert sum(subject["num_hits"] for subject in result.chosen_hits.values()) >= 41


def test_portuguese_constraints_apply_to_joint_choice(standard_scores):
    result = optimization(
        course="Curso de teste",
        min_AC=100.0,
        std_scores=standard_scores,
        constraints_dict={"PORT_RED": [[">=", 12], ["<=", 12]]},
        min_subjects=[],
        essay_options=[{"raw_score": 10.0, "standard_score": 500.0}],
        port_red_objective="none",
    )

    assert result.chosen_hits["PORT_RED"]["num_hits"] == 12


@pytest.mark.parametrize(
    ("objective", "expected_hits", "expected_essay"),
    [
        ("portuguese", 1, None),
        ("combined", 1, 4.5),
    ],
)
def test_port_red_objectives_are_independent(standard_scores, objective, expected_hits, expected_essay):
    result = optimization(
        course="Curso de teste",
        min_AC=100.0,
        std_scores=standard_scores,
        constraints_dict={},
        min_subjects=[],
        essay_options=[
            {"raw_score": 4.5, "standard_score": 250.0},
            {"raw_score": 10.0, "standard_score": 500.0},
        ],
        port_red_objective=objective,
    )

    assert result.chosen_hits["PORT_RED"]["num_hits"] == expected_hits
    if expected_essay is not None:
        assert result.chosen_hits["PORT_RED"]["essay_score"] == expected_essay


def test_legacy_port_red_min_subject_is_rejected(standard_scores):
    with pytest.raises(ValueError, match="port_red_objective"):
        optimization(
            course="Curso de teste",
            min_AC=100.0,
            std_scores=standard_scores,
            constraints_dict={},
            min_subjects=["PORT_RED"],
            essay_options=[{"raw_score": 10.0, "standard_score": 500.0}],
        )
