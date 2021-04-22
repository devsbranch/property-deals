# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json
from datetime import date
from flask import render_template, redirect, url_for, request, flash, current_app, g, current_app
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from app import db, redis_client
from app.base.models import Property
from app.home import blueprint
from app.tasks import image_process, delete_img_obj


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
