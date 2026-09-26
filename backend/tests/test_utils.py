from src.utils import getGraphData


def test_get_graph_data_normalizes_historical_course_name():
    historical_name = getGraphData(2022, "Ciência da Computação", "LI_EP")
    canonical_name = getGraphData(
        2022, "Ciência da Computação - Bacharelado", "LI_EP"
    )

    assert historical_name
    assert historical_name == canonical_name
