import os

from flask import jsonify, send_from_directory

from server import app


@app.route("/health")
def health():
    """health route"""
    state = {"status": "UP"}
    return jsonify(state)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon/favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@app.route('/robots.txt')
def robots():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'robots.txt'
    )
