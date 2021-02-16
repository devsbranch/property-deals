def validate_add_user_data(data_dict):
    fields = ["username", "email", "password"]
    for field in fields:
        if field not in data_dict:
            return False
        return True
