import json
from flask import render_template, request, send_from_directory

def setup_routes(app, dispatcher, path):
    @app.route('/editor/<path:path>')
    def editor_files(path):
        return send_from_directory('editor', path)

    # /api/v1/editor/
    @app.route(path)
    def editor_index():
        data = request.args.get('json', )
        if data :
            json_value = json.loads(data)
            result = dispatcher.dispatch(json_value)
        else:
            result = ''
        data = data or """
{
    "Hello": {
        "result": {
            "world": "String"
        }
    }
}
        """
        return render_template('index.html', json=data, result=result)
