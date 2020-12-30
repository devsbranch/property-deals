# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
import os
from app.home import blueprint
from flask import render_template, redirect, url_for, request, current_app, flash
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound
from app.base.forms import PropertyForm
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


@blueprint.route('/create-property', methods=['GET', 'POST'])
def create_property():
    form = PropertyForm()
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
    return render_template('create_property.html', form=form)


@blueprint.route('/view-properties')
def view_properties():
    """
    This function returns the view_properties.html the properties and images from the database.
    Only one picture for each property is needed to be displayed on each property in the view_properties.html page.
    So a dictionary is used to return each id(property_id) as a key and property image(image_name) as value.
    """
    properties = db.session.query(Property).order_by(Property.date.desc())
    property_images = db.session.query(PropertyImage).order_by(PropertyImage.id.asc())

    pictures = {}
    for property_img in property_images:
        pictures[property_img.property_id] = property_img.image_name

    return render_template('view_properties.html',
                           properties=properties,
                           property_images=property_images,
                           pictures=pictures)


@blueprint.route('/<int:prop_id>/details')
def prop_details(prop_id):

    prop_info = Property.query.filter_by(id=prop_id).first()
    prop_images = PropertyImage.query.filter_by(property_id=prop_info.id).order_by(PropertyImage.id.desc())

    return render_template('property.html', prop_info=prop_info, prop_images=prop_images)


@blueprint.route('/<int:prop_id>/delete', methods=['POST'])
@login_required
def delete(prop_id):
    """
    This function is called when the delete button is clicked, the id of the property
    is used to query the property to delete including images related to the property from the database.
    The os.remove() function is also used to delete the images in the file system
    """
    property_to_del = Property.query.get_or_404(prop_id)
    images_to_del = PropertyImage.query.filter_by(property_id=property_to_del.id)

    db.session.delete(property_to_del)

    for img in images_to_del:
        db.session.delete(img)
        file_path = os.path.join(current_app.root_path, 'base/static/property_images', img.image_name)
        os.remove(file_path)

    db.session.commit()

    flash('Proper deleted')
    return redirect(url_for('home_blueprint.view_properties'))
