from flask import send_from_directory

def setup_routes(app):
    @app.route('/static/<path:path>')
    def send_images(path):
        return send_from_directory('static', path)
