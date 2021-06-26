from flask import Response


def welcome():
    response_text = '{ "message": "Hello, welcome to the Property Deals flask-api" }'
    response = Response(response_text, 200, mimetype='application/json')
    return response


def health():
    response_text = '{"status": "OK"}'
    response = Response(response_text, 200, mimetype="application/json")
    return response
