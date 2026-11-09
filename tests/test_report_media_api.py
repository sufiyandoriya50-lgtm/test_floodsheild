"""tests that it 
Uploads valid photograph.
Rejects unsupported file.
Retrieves photograph metadata.
Retrieves actual image.
Deletes photograph."""
import io ,os,pytest
from PIL import Image
from app.extensions import db
from app.models.user import User
from app.models.flood_report import FloodReport
from app.models.report_media import FloodReportMedia
from flask_jwt_extended import create_access_token

# Generates a real, valid PNG image in memory for automated upload tests.
def create_test_png():
    image_buffer = io.BytesIO()

    image = Image.new("RGB", (10, 10), color="blue")
    image.save(image_buffer, format="PNG")

    image_buffer.seek(0)
    return image_buffer
# Tests whether the API returns the photographs attached to a flood report.

# Creates a test citizen and a flood report for photograph-upload tests.
@pytest.fixture()
def test_report(app):
    with app.app_context():
        user = User(
            name="Media Test User",
            email="media-test@example.com"
        )

        user.set_password("TestPassword123")

        db.session.add(user)
        db.session.flush()

        report = FloodReport(
            user_id=user.id,
            latitude=23.0225,
            longitude=72.5714,
            water_depth_cm=25,
            description="Test waterlogging report",
            status="pending"
        )

        db.session.add(report)
        db.session.commit()

        return report.id
def test_get_report_photos(auth_client, app, test_report):
    image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20

    upload_response = auth_client.post(
        f"/api/reports/{test_report}/media",
        data={
            "photos": (
                 create_test_png(),
                "waterlogging.png"
             )
        },
        content_type="multipart/form-data"
    )

    assert upload_response.status_code == 201

    response = auth_client.get(
        f"/api/reports/{test_report}/media"
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["count"] == 1
    assert response_data["data"][0]["original_filename"] == (
        "waterlogging.png"
    )
    assert "image_url" in response_data["data"][0]
# Tests whether the image endpoint returns the actual stored image bytes.
# Tests whether the image endpoint returns the exact uploaded image bytes.
def test_view_report_photo(auth_client, test_report):
    image_file = create_test_png()

    # Save the original generated PNG bytes before uploading.
    expected_image_bytes = image_file.getvalue()

    upload_response = auth_client.post(
        f"/api/reports/{test_report}/media",
        data={
            "photos": (
                image_file,
                "waterlogging.png"
            )
        },
        content_type="multipart/form-data"
    )

    assert upload_response.status_code == 201

    media_id = upload_response.get_json()["data"][0]["media_id"]

    # Request the actual photograph from the backend.
    response = auth_client.get(
        f"/api/reports/{test_report}/media/{media_id}"
    )

    assert response.status_code == 200

    # Compare the returned image against the original uploaded PNG.
    assert response.data == expected_image_bytes

    assert response.mimetype == "image/png"
# Tests whether deleting a photograph removes its database record and physical file.
def test_delete_report_photo(auth_client, app, test_report):
    image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20

    upload_response = auth_client.post(
        f"/api/reports/{test_report}/media",
        data={
            "photos": (
                 create_test_png(),
                "waterlogging.png"
             )
        },
        content_type="multipart/form-data"
    )

    assert upload_response.status_code == 201

    media_id = upload_response.get_json()["data"][0]["media_id"]

    with app.app_context():
        media = db.session.get(FloodReportMedia, media_id)
        saved_file = os.path.join(
            app.instance_path,
            media.file_path
        )

        assert os.path.exists(saved_file)

    # Send the DELETE request to remove the photograph.
    response = auth_client.delete(
        f"/api/reports/{test_report}/media/{media_id}"
    )

    assert response.status_code == 200

    with app.app_context():
        deleted_media = db.session.get(
            FloodReportMedia,
            media_id
        )

        assert deleted_media is None
        assert not os.path.exists(saved_file)

# Tests whether an image with a fake PNG extension is rejected.
def test_reject_fake_png(auth_client, test_report):
    fake_image = io.BytesIO(b"This is not a real PNG image")

    response = auth_client.post(
        f"/api/reports/{test_report}/media",
        data={
            "photos": (
                fake_image,
                "fake.png"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


# Tests whether an image larger than the allowed 5 MB is rejected.
def test_reject_oversized_image(auth_client, test_report):
    oversized_image = io.BytesIO(b"A" * (5 * 1024 * 1024 + 1))

    response = auth_client.post(
        f"/api/reports/{test_report}/media",
        data={
            "photos": (
                oversized_image,
                "large.png"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"

# Verifies that a citizen cannot upload photos to another citizen's report.
def test_other_user_cannot_upload_photo(app, test_report):

    # Step 1: Create a second citizen.
    with app.app_context():
        other_user = User(
            name="Second Test User",
            email="second_test@example.com"
        )
        other_user.set_password("TestPassword123")

        db.session.add(other_user)
        db.session.commit()

        other_user_id = other_user.id

        # Step 2: Generate a JWT for the second citizen.
        token = create_access_token(
            identity=str(other_user_id)
        )

    # Step 3: Create a separate authenticated test client.
    client = app.test_client()

    # Step 4: Generate a valid image.
    image_file = create_test_png()

    # Step 5: Attempt to upload to the first citizen's report.
    response = client.post(
        f"/api/reports/{test_report}/media",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "photos": (
                image_file,
                "unauthorized_photo.png"
            )
        },
        content_type="multipart/form-data"
    )

    # Step 6: Verify that the backend rejects the upload.
    assert response.status_code == 403   

# Verifies that a citizen cannot delete a photo attached to another citizen's report.
def test_other_user_cannot_delete_photo(app, test_report):
    from flask_jwt_extended import create_access_token
    from app.models.user import User
    from app.models.report_media import FloodReportMedia
    from app.extensions import db

    # Create a second citizen who does not own the report.
    with app.app_context():
        other_user = User(
            name="Second Test User",
            email="second_test@example.com"
        )
        other_user.set_password("TestPassword123")
        db.session.add(other_user)
        db.session.commit()

        token = create_access_token(identity=str(other_user.id))

    client = app.test_client()

# Creates a JWT for the test user who owns the flood report.
def create_owner_token(app):
    from flask_jwt_extended import create_access_token

    with app.app_context():
        return create_access_token(identity="1")

    # First, upload a photo as the report owner using the authenticated test client.
    image_file = create_test_png()
    owner_response = client.post(
        f"/api/reports/{test_report}/media",
        headers={"Authorization": f"Bearer {create_owner_token(app)}"},
        data={"photos": (image_file, "owner_photo.png")},
        content_type="multipart/form-data"
    )

    assert owner_response.status_code == 201

    media_id = owner_response.get_json()["media"][0]["id"]

    # The second citizen attempts to delete the owner's photo.
    response = client.delete(
        f"/api/reports/{test_report}/media/{media_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
