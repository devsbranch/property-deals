from marshmallow import fields
from app import ma


class PropertySchema(ma.Schema):
    id = fields.Integer()
    name = fields.String(required=True)
    desc = fields.String(required=True)
    date_listed = fields.DateTime()
    price = fields.String(required=True)
    location = fields.String(required=True)
    images_folder = fields.String()
    photos = fields.String()
    photos_location = fields.String()
    type = fields.String(required=True)
    is_available = fields.Boolean()
    deal_done = fields.Boolean()
    user_id = fields.Integer(required=True)


listing_schema = PropertySchema()
listings_schema = PropertySchema(many=True)
