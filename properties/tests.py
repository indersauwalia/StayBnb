from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from users.models import Profile
from .models import Property, PropertyImage


class PropertyDiscoveryTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username="host", password="test-password-123")
        self.cabin = Property.objects.create(
            host=self.host,
            title="Pine Quiet",
            description="A quiet cabin among the trees.",
            location="Manali",
            property_type=Property.CABIN,
            price_per_night=4500,
        )
        Property.objects.create(
            host=self.host,
            title="City Light",
            description="A sunny city apartment.",
            location="Jaipur",
            property_type=Property.APARTMENT,
            price_per_night=6500,
        )

    def tearDown(self):
        for image in PropertyImage.objects.all():
            image.image.delete(save=False)

    def test_search_filters_location_type_and_price(self):
        response = self.client.get(reverse("properties:home"), {
            "location": "man",
            "type": Property.CABIN,
            "max_price": "5000",
        })

        self.assertEqual(list(response.context["listings"]), [self.cabin])

    def test_property_detail_renders(self):
        response = self.client.get(self.cabin.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pine Quiet")
        self.assertContains(response, "Manali")

    def test_invalid_price_filter_does_not_break_discovery(self):
        response = self.client.get(reverse("properties:home"), {"min_price": "not-a-price"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a number")
        self.assertEqual(len(response.context["listings"]), 2)

    def test_host_can_publish_listing_with_multiple_images(self):
        Profile.objects.create(user=self.host, role=Profile.HOST)
        self.client.force_login(self.host)
        image_data = BytesIO()
        Image.new("RGB", (12, 12), color="olive").save(image_data, format="JPEG")
        image_bytes = image_data.getvalue()
        response = self.client.post(reverse("properties:create"), {
            "title": "A little hideaway",
            "description": "A quiet place to land.",
            "location": "Coorg",
            "property_type": Property.CABIN,
            "price_per_night": "5400.00",
            "amenities": "Fireplace, Garden",
            "images": [
                SimpleUploadedFile("one.jpg", image_bytes, content_type="image/jpeg"),
                SimpleUploadedFile("two.jpg", image_bytes, content_type="image/jpeg"),
            ],
        })

        self.assertEqual(response.status_code, 302)
        images = PropertyImage.objects.filter(property__title="A little hideaway")
        self.assertEqual(images.count(), 2)
        removed_file = images.first().image.name

        response = self.client.post(reverse("properties:edit", args=[images.first().property_id]), {
            "title": "A little hideaway",
            "description": "A quiet place to land.",
            "location": "Coorg",
            "property_type": Property.CABIN,
            "price_per_night": "5400.00",
            "amenities": "Fireplace, Garden",
            "delete_images": [images.first().pk],
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PropertyImage.objects.filter(property__title="A little hideaway").count(), 1)
        self.assertFalse(images.first().image.storage.exists(removed_file))
