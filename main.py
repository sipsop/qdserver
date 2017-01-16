import ssl
from flask import Flask
from flask_uwsgi_websocket import GeventWebSocket
from qdserver.qdserver import setup_routes

import gevent.monkey
gevent.monkey.patch_all()

dev = True
debug = True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fjdskajfi;ji83faifhisahghy38pp12y2891yfehpfPP}#@(*&&#(&(!)))'

sockets = None
sockets = GeventWebSocket(app)
setup_routes(app, sockets, dev=dev)

if __name__ == '__main__':
    import qdweb.routes
    qdweb.routes.setup_routes(app)

    # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    # context.load_cert_chain('yourserver.crt', 'yourserver.key')
    app.run(host='0.0.0.0', port=9000, debug=debug)
