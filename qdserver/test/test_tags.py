from qdserver import run_query, model

model.setup_testing_mode()

def test_query1():
    tags = run_query({
        "Tags": {
            "args": {
                "barID":    "bar_id_here",
            },
            "result": {
                "tagInfo": [{
                    "tagID":    "String",
                    "tagName":  "String",
                    "excludes": [
                        "String",
                    ],
                }],
                "tagGraph": [{
                    "srcID":  "String",
                    "dstIDs": ["String"],
                }],
            },
        },
    })
    tags = tags['result']

    assert tags['tagInfo']
    assert tags['tagGraph']
    assert len([edge['srcID'] for edge in tags['tagGraph'] if edge['srcID'] == '#beer']) == 1

    # TODO: More testing


if __name__ == '__main__':
    test_query1()
