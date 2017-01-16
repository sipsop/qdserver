from .qdserver import setup_dispatcher
dispatcher = setup_dispatcher(dev=True)

run_query = dispatcher.dispatch
run_feed  = dispatcher.dispatch_feed

def run_test_query(query):
    query = dict(query)
    print("testing query", query)
    expect = query.pop('expect')
    result = run_query(query)
    assert result == expect, (result, expect)


def run_test_queries(queries):
    for query in queries:
        run_test_query(query)
