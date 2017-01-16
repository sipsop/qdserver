import pytest
from qdserver import run_query, model
model.setup_testing_mode()

@pytest.mark.skip(reason="multiple queries not supported")
def test_multiple_queries():
    result = run_query({
        "Hello": {
            "result": {
                "world": "String"
            }
        },
        "Tags": {
            "args": {
                "barID":    "bar_id_here",
            },
            "result": {
                "tagGraph": [{
                    "srcID":  "String",
                    "dstIDs": ["String"],
                }],
            },
        },
    })
    assert 'results' in result
    query_results = result['results']

    assert 'Hello' in query_results
    assert query_results['Hello']['world'] == 'Hello World!'

    assert 'Tags' in query_results
    assert 'tagGraph' in query_results['Tags']
