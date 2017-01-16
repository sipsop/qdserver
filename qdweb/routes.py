from flask import send_from_directory
# from .auth import auth0

def setup_routes(app):
    # auth0.setup_routes(app)

    @app.route('/', defaults={'path': 'index.html'})
    @app.route('/<path:path>')
    def send_index(path):
        return send_from_directory('web', path)
