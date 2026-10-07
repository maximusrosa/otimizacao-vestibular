from src.utils import normalizeCourseName


def test_normalize_historical_course_name():
    assert normalizeCourseName("Ciência da Computação") == "Ciência da Computação - Bacharelado"
