import sys
import rethinkdb as r

from qdserver import model

def try_reql(query, message):
    try:
        model.run(query)
    except r.ReqlError:
        print(message)

def create_db(db_name):
    try_reql(r.db_create(db_name), 'Database %r already exists' % db_name)

def create_table(db_name, table_name):
    try_reql(r.db(db_name).table_create(table_name), 'Database %r already exists' % table_name)

if __name__ == '__main__':
    if '--test' in sys.argv:
        model.setup_testing_mode()

    create_db('qdodger')
    create_table('qdodger', 'MenuItemDefs')
    create_table('qdodger', 'Orders')
    create_table('qdodger', 'MenuItems')
    create_table('qdodger', 'UserProfiles')
    create_table('qdodger', 'Bars')
