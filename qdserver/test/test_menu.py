from qdserver import run_query, model
model.setup_testing_mode()

SubMenuQuery = {
    "image":     "String",
    "menuItems": [{
        "id":     "String",
        "name":   "String",
        "images": ["String"],
        "tags":   ["String"],
    }],
}

def test_query1():
    query({
        "Menu": {
            "args": {
                "barID": "bar_id_here",
            },
            "result": {
                "barID": "String",
                "beer": SubMenuQuery,
            },
        },
    })

def test_query2():
    query({
        "fragments": {
            "SubMenu": SubMenuQuery,
        },
        "Menu": {
            "args": {
                "barID": "bar_id_here",
            },
            "result": {
                "barID": "String",
                "beer":  "SubMenu",
                "wine":  "SubMenu",
            },
        },
    })

def query(q):
    result = run_query(q)
    menu = result['result']
    assert menu['barID'] == 'bar_id_here'
    assert menu['beer']['image']

    menuItem = menu['beer']['menuItems'][0]
    assert menuItem['id']
    assert menuItem['name']
    assert menuItem['images']
    assert menuItem['tags']


if __name__ == '__main__':
    test_query1()
    test_query2()
