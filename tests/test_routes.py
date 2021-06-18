from tests.conftest import test_user_data


def login(test_client, username, password):
    return test_client.post(
        "/login", data=dict(username=username, password=password), follow_redirects=True
    )


def logout(test_client):
    return test_client.get("/logout", follow_redirects=True)


def test_home_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

    # "Create Property" and "My Listings" are only available if user has logged in.
    assert b"Create Property" and b"My Listings" not in response.data


def test_registration(test_client):
    """
    Test if the registration functionality works.
    GIVEN a Flask application
    WHEN the '/register' page is requested (POST)
    THEN check the response is valid, check that the flash message ("Your account has been created. Check your inbox to
    verify your email.") attribute is present in the html.
    """
    response = test_client.post("/register", data=test_user_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Sign in" in response.data
    assert (
        b"Your account has been created. Check your inbox to verify your email."
        in response.data
    )


def test_login(test_client):
    """
    GIVEN a Flask application
    WHEN the '/login' page is requested (POST)
    THEN check the response is valid, check that the attributes in the html available to a logged in user are present
    """
    response = login(
        test_client,
        username=test_user_data["username"],
        password=test_user_data["password"],
    )
    assert response.status_code == 200

    # The attributes below should be available in the html if the user has logged in
    assert b"Create Property" and b"My Listings" in response.data
    assert b"My Profile" and b"Logout" in response.data
