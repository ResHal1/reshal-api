import pytest
from faker import Faker
from pydantic import ValidationError

from reshal_api.facility.schemas import FacilityBase, FacilityUpdate

fake = Faker()

schemas = [FacilityBase, FacilityUpdate]


@pytest.mark.parametrize("Schema", schemas)
@pytest.mark.parametrize(
    "lat, is_valid",
    (
        (-90, True),
        (0, True),
        (90, True),
        (fake.latitude(), True),
        (-91, False),
        (91, False),
    ),
)
def test_lat_validatos(
    Schema: type[FacilityBase | FacilityUpdate], lat: float, is_valid: bool
):
    data = {
        "name": fake.first_name(),
        "lat": lat,
        "lon": fake.longitude(),
        "address": fake.address(),
        "price": 10,
        "image_url": fake.url(),
    }

    if isinstance(Schema, FacilityUpdate):
        data["type_id"] = fake.uuid4()

    if is_valid:
        try:
            Schema(**data)
        except ValidationError:
            pytest.fail(f"Latitude {lat!r} should be valid")
    else:
        with pytest.raises(ValidationError) as exc_info:
            Schema(**data)
        assert "Latitude must be between -90 and 90" in str(exc_info.value)


@pytest.mark.parametrize("Schema", schemas)
@pytest.mark.parametrize(
    "lon, is_valid",
    (
        (-180, True),
        (0, True),
        (180, True),
        (fake.longitude(), True),
        (-181, False),
        (181, False),
    ),
)
def test_lon_validatos(
    Schema: type[FacilityBase | FacilityUpdate], lon: float, is_valid: bool
):
    data = {
        "name": fake.first_name(),
        "lat": fake.latitude(),
        "lon": lon,
        "address": fake.address(),
        "price": 10,
        "image_url": fake.url(),
    }

    if isinstance(Schema, FacilityUpdate):
        data["type_id"] = fake.uuid4()

    if is_valid:
        try:
            Schema(**data)
        except ValidationError:
            pytest.fail(f"Longitude {lon!r} should be valid")
    else:
        with pytest.raises(ValidationError) as exc_info:
            Schema(**data)
        assert "Longitude must be between -180 and 180" in str(exc_info.value)
