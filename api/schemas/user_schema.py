add_user_schema = {
    "type": "object",
    "properties": {
        "first_name": {"type": "string", "minLength": 3, "maxLength": 30},
        "last_name": {"type": "string", "minLength": 3, "maxLength": 30},
        "other_name": {"type": "string", "minLength": 3, "maxLength": 30},
        "gender": {"type": "string", "minLength": 4, "maxLength": 7},
        "phone": {"type": "string", "minLength": 10, "maxLength": 12},
        "username": {"type": "string", "minLength": 2, "maxLength": 20},
        "email": {"type": "string", "minLength": 3, "maxLength": 30},
        "password": {"type": "string", "minLength": 8, "maxLength": 60}
    },
    "required": ["first_name", "last_name", "gender", "phone", "username", "email", "password"]
}
