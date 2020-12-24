# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
import os
from app.home import blueprint
from flask import render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound
from app.base.forms import ListPropertyForm
from app.base.models import Property, PropertyImage
from app import db
from werkzeug.utils import secure_filename


@blueprint.route('/index')
@login_required
def index():
    return render_template('index.html', segment='index')


@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template(template, segment=segment)

    except TemplateNotFound:
        return render_template('page-404.html'), 404

    except:
        return render_template('page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):
    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None


@blueprint.route('/list-property', methods=['GET', 'POST'])
def create_listing():
    form = ListPropertyForm()
    if request.method == 'POST':
        prop_info = Property(property_name=form.prop_name.data,
                             property_desc=form.prop_desc.data,
                             property_price=form.prop_price.data,
                             property_location=form.prop_location.data,
                             user_id=current_user.id)

        db.session.add(prop_info)
        db.session.commit()

        # gets image files as a list uploaded by user in the form
        img_files = request.files.getlist('prop_photos')

        # get the id of the recently added property by current_user and use
        # it to link the image files to that property.
        get_prop_id = db.session.query(Property).order_by(Property.date.desc())

        # saves image files uploaded to app/base/static/property_images/
        for img_file in img_files:
            filename = secure_filename(img_file.filename)

            # replace spaces in filename with underscore
            clean_filename = filename.replace(' ', '_')
            prop_images = PropertyImage(image_name=clean_filename,
                                        property_id=get_prop_id[0].id)
            db.session.add(prop_images)
            db.session.commit()

            file_path = os.path.join(current_app.root_path, 'base/static/property_images', clean_filename)
            img_file.save(file_path)

        return redirect(url_for('base_blueprint.route_default'))
    return render_template('create_listing.html', form=form)