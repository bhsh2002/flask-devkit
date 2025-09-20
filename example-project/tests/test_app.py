from showcase_app import create_app


def test_app_creation():
    """
    Tests that the Flask app is created successfully without errors.
    """
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-secret",
        }
    )
    assert app is not None


def test_posts_endpoint_exists(client):
    """
    Tests that the /posts/ endpoint is available under the main API prefix.
    """
    response = client.get("/api/v1/posts/")
    # Should be accessible to the public
    assert response.status_code == 200


def test_user_endpoints_are_public(client):
    """
    Tests that the user list endpoint is public as configured in create_app.
    """
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
