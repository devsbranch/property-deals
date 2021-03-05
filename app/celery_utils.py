import json
from app import celery
from app.base.file_handler import property_image_handler


@celery.task()
def save_property_data(temp_folder, form_data):
    from app.base.models import Property

    prop_images_dir, images_list = property_image_handler(temp_folder)
    img_list_to_json = json.dumps(images_list)
    prop_images = {"photos": img_list_to_json, "image_folder": prop_images_dir}
    form_data.update(prop_images)
    Property.add_property(form_data)
    return "Property Created"


@celery.task()
def update_prop_images(temp_folder, prop_id):
    from app.base.models import Property

    prop_images_dir, images_list = property_image_handler(temp_folder)
    img_list_to_json = json.dumps(images_list)
    Property.update_property_images(prop_images_dir, img_list_to_json, prop_id)
    return "Images Updated"
