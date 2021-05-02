# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, request
from jinja2 import TemplateNotFound
from app.home import blueprint


@blueprint.route("/index")
def index():
    return render_template(
        "index.html",
        segment="index"
    )


@blueprint.route("/<template>")
def route_template(template):
    try:

        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template(template, segment=segment)

    except TemplateNotFound:
        return render_template("errors/404.html"), 404


# Helper - Extract current page name from request
def get_segment(request):
    try:

        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None
