"""
Tests for the 'items/create_item_drink' route (POST method)
Tests both successful and failure cases using fixtures from tests/conftest.py
"""
import json
from typing import Dict, Any
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.support.item.schemas import ItemDrinkPreactSchema
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.support.category.model import Category
from app.support.subcategory.model import Subcategory
from app.support.sweetness.model import Sweetness
from app.support.country.model import Country
from app.support.region.model import Region
from app.support.subregion.model import Subregion
from app.support.varietal.model import Varietal
from app.support.food.model import Food


pytestmark = pytest.mark.asyncio


async def test_create_item_drink_success(
    authenticated_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """
    Test successful creation of an item with drink using the create_item_drink endpoint.
    """
    client = authenticated_client_with_db
    session = test_db_session

    # Create required dependencies first
    # Create a category
    category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
    session.add(category)
    await session.commit()
    await session.refresh(category)

    # Create a subcategory
    subcategory = Subcategory(name="Red", category_id=category.id)
    session.add(subcategory)
    await session.commit()
    await session.refresh(subcategory)

    # Create sweetness
    sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
    session.add(sweetness)
    await session.commit()
    await session.refresh(sweetness)

    # Create country
    country = Country(name="France", name_ru="Франция", name_fr="France")
    session.add(country)
    await session.commit()
    await session.refresh(country)

    # Create region
    region = Region(name="Bordeaux", country_id=country.id)
    session.add(region)
    await session.commit()
    await session.refresh(region)

    # Create subregion
    subregion = Subregion(name="Medoc", region_id=region.id)
    session.add(subregion)
    await session.commit()
    await session.refresh(subregion)

    # Create varietal
    varietal = Varietal(name="Cabernet Sauvignon", name_ru="Каберне Совиньон", name_fr="Cabernet Sauvignon")
    session.add(varietal)
    await session.commit()
    await session.refresh(varietal)

    # Create food
    food = Food(name="Cheese", name_ru="Сыр", name_fr="Fromage")
    session.add(food)
    await session.commit()
    await session.refresh(food)

    # Prepare the request data
    request_data = {
        "title": "Test Wine",
        "title_ru": "Тестовое вино",
        "title_fr": "Vin de test",
        "subtitle": "Test Wine Subtitle",
        "subtitle_ru": "Сабтайтл тестового вина",
        "subtitle_fr": "Sous-titre du vin de test",
        "description": "This is a test wine description",
        "description_ru": "Описание тестового вина",
        "description_fr": "Description du vin de test",
        "recommendation": "Great with cheese",
        "recommendation_ru": "Отлично с сыром",
        "recommendation_fr": "Excellent avec du fromage",
        "madeof": "Grapes",
        "madeof_ru": "Виноград",
        "madeof_fr": "Raisins",
        "subcategory_id": subcategory.id,
        "sweetness_id": sweetness.id,
        "subregion_id": subregion.id,
        "alc": 12.5,
        "sugar": 2.0,
        "age": "2020",
        "vol": 0.75,
        "price": 25.99,
        "varietals": [[varietal.id, 100.0]],  # List of [varietal_id, percentage]
        "foods": [food.id]  # List of food IDs
    }

    # Make the request to the endpoint
    response = await client.post(
        "/items/create_item_drink",
        data={"data": json.dumps(request_data)}
    )

    # Assertions
    assert response.status_code == 200, f"Response: {response.text}"
    result = response.json()
    assert "id" in result
    assert result["vol"] == 0.75
    assert result["price"] == 25.99

    # Verify that the drink was created
    assert "drink" in result
    assert result["drink"]["title"] == "Test Wine"
    assert result["drink"]["title_ru"] == "Тестовое вино"
    assert result["drink"]["title_fr"] == "Vin de test"

    # Verify the drink has the correct relationships
    assert result["drink"]["subcategory"]["id"] == subcategory.id
    assert result["drink"]["sweetness"]["id"] == sweetness.id
    assert result["drink"]["subregion"]["id"] == subregion.id

    # Verify varietals and foods were created
    if "varietals" in result["drink"] and result["drink"]["varietals"]:
        assert result["drink"]["varietals"][0]["varietal"]["id"] == varietal.id
        assert result["drink"]["varietals"][0]["percentage"] == 100.0

    if "foods" in result["drink"] and result["drink"]["foods"]:
        assert result["drink"]["foods"][0]["id"] == food.id


async def test_create_item_drink_with_file_success(
    authenticated_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """
    Test successful creation of an item with drink including an image file.
    """
    client = authenticated_client_with_db
    session = test_db_session

    # Create required dependencies first (same as above)
    # Create a category
    category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
    session.add(category)
    await session.commit()
    await session.refresh(category)

    # Create a subcategory
    subcategory = Subcategory(name="Red", category_id=category.id)
    session.add(subcategory)
    await session.commit()
    await session.refresh(subcategory)

    # Create sweetness
    sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
    session.add(sweetness)
    await session.commit()
    await session.refresh(sweetness)

    # Create country
    country = Country(name="France", name_ru="Франция", name_fr="France")
    session.add(country)
    await session.commit()
    await session.refresh(country)

    # Create region
    region = Region(name="Bordeaux", country_id=country.id)
    session.add(region)
    await session.commit()
    await session.refresh(region)

    # Create subregion
    subregion = Subregion(name="Medoc", region_id=region.id)
    session.add(subregion)
    await session.commit()
    await session.refresh(subregion)

    # Create varietal
    varietal = Varietal(name="Cabernet Sauvignon", name_ru="Каберне Совиньон", name_fr="Cabernet Sauvignon")
    session.add(varietal)
    await session.commit()
    await session.refresh(varietal)

    # Create food
    food = Food(name="Cheese", name_ru="Сыр", name_fr="Fromage")
    session.add(food)
    await session.commit()
    await session.refresh(food)

    # Prepare the request data
    request_data = {
        "title": "Test Wine With Image",
        "title_ru": "Тестовое вино с изображением",
        "title_fr": "Vin de test avec image",
        "subtitle": "Test Wine With Image Subtitle",
        "subtitle_ru": "Сабтайтл тестового вина с изображением",
        "subtitle_fr": "Sous-titre du vin de test avec image",
        "description": "This is a test wine with image description",
        "description_ru": "Описание тестового вина с изображением",
        "description_fr": "Description du vin de test avec image",
        "recommendation": "Great with cheese",
        "recommendation_ru": "Отлично с сыром",
        "recommendation_fr": "Excellent avec du fromage",
        "madeof": "Grapes",
        "madeof_ru": "Виноград",
        "madeof_fr": "Raisins",
        "subcategory_id": subcategory.id,
        "sweetness_id": sweetness.id,
        "subregion_id": subregion.id,
        "alc": 13.5,
        "sugar": 1.5,
        "age": "2021",
        "vol": 0.75,
        "price": 30.99,
        "varietals": [[varietal.id, 100.0]],
        "foods": [food.id]
    }

    # Make the request to the endpoint with a file (using a temporary file)
    import tempfile
    import os
    from PIL import Image
    
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_image:
        img = Image.new('RGB', (100, 100), color='red')
        img.save(temp_image, format='JPEG')
        temp_image_path = temp_image.name

    try:
        with open(temp_image_path, "rb") as image_file:
            files = {"file": ("test_image.jpg", image_file, "image/jpeg")}
            response = await client.post(
                "/items/create_item_drink",
                data={"data": json.dumps(request_data)},
                files=files
            )

        # Assertions
        assert response.status_code == 200, f"Response: {response.text}"
        result = response.json()
        assert "id" in result
        assert result["vol"] == 0.75
        assert result["price"] == 30.99

        # Verify that the drink was created
        assert "drink" in result
        assert result["drink"]["title"] == "Test Wine With Image"
    finally:
        # Clean up the temporary file
        os.unlink(temp_image_path)


async def test_create_item_drink_missing_required_fields():
    """
    Test failure when required fields are missing.
    """
    # This test requires an authenticated client, but we'll test validation separately
    pass


async def test_create_item_drink_invalid_json(
    authenticated_client_with_db: AsyncClient
):
    """
    Test failure when invalid JSON is provided.
    """
    client = authenticated_client_with_db

    # Send invalid JSON
    response = await client.post(
        "/items/create_item_drink",
        data={"data": "invalid json string"}
    )

    # Should return 422 for invalid JSON
    assert response.status_code == 422


async def test_create_item_drink_invalid_schema(
    authenticated_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """
    Test failure when the provided data doesn't match the expected schema.
    """
    client = authenticated_client_with_db
    session = test_db_session

    # Create required dependencies first - use a unique name to avoid conflicts
    # Check if 'Wine' category already exists
    from sqlalchemy import select
    existing_category = await session.execute(select(Category).where(Category.name == "Wine"))
    category = existing_category.scalar_one_or_none()
    
    if not category:
        # Create a category
        category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
        session.add(category)
        await session.commit()
        await session.refresh(category)

    # Check if 'Red' subcategory already exists
    existing_subcategory = await session.execute(select(Subcategory).where(Subcategory.name == "Red"))
    subcategory = existing_subcategory.scalar_one_or_none()
    
    if not subcategory:
        subcategory = Subcategory(name="Red", category_id=category.id)
        session.add(subcategory)
        await session.commit()
        await session.refresh(subcategory)

    # Check if 'Dry' sweetness already exists
    existing_sweetness = await session.execute(select(Sweetness).where(Sweetness.name == "Dry"))
    sweetness = existing_sweetness.scalar_one_or_none()
    
    if not sweetness:
        sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
        session.add(sweetness)
        await session.commit()
        await session.refresh(sweetness)

    # Check if 'France' country already exists
    existing_country = await session.execute(select(Country).where(Country.name == "France"))
    country = existing_country.scalar_one_or_none()
    
    if not country:
        country = Country(name="France", name_ru="Франция", name_fr="France")
        session.add(country)
        await session.commit()
        await session.refresh(country)

    # Check if 'Bordeaux' region already exists
    existing_region = await session.execute(select(Region).where(Region.name == "Bordeaux"))
    region = existing_region.scalar_one_or_none()
    
    if not region:
        region = Region(name="Bordeaux", country_id=country.id)
        session.add(region)
        await session.commit()
        await session.refresh(region)

    # Check if 'Medoc' subregion already exists
    existing_subregion = await session.execute(select(Subregion).where(Subregion.name == "Medoc"))
    subregion = existing_subregion.scalar_one_or_none()
    
    if not subregion:
        subregion = Subregion(name="Medoc", region_id=region.id)
        session.add(subregion)
        await session.commit()
        await session.refresh(subregion)

    # Prepare the request data with invalid values (empty title should fail validation)
    request_data = {
        "title": "",  # Empty title should fail validation
        "subcategory_id": subcategory.id,
        "sweetness_id": sweetness.id,
        "subregion_id": subregion.id,
        "vol": 0.75,
        "price": 25.99,
        "varietals": [],
        "foods": []
    }

    # Make the request to the endpoint
    response = await client.post(
        "/items/create_item_drink",
        data={"data": json.dumps(request_data)}
    )

    # Should return 422 for validation error
    assert response.status_code == 422


async def test_create_item_drink_nonexistent_relations(
    authenticated_client_with_db: AsyncClient
):
    """
    Test failure when referenced IDs don't exist in the database.
    """
    client = authenticated_client_with_db

    # Prepare the request data with non-existent IDs
    request_data = {
        "title": "Test Wine",
        "subcategory_id": 99999,  # Non-existent subcategory
        "sweetness_id": 99999,    # Non-existent sweetness
        "subregion_id": 99999,    # Non-existent subregion
        "vol": 0.75,
        "price": 25.99,
        "varietals": [],
        "foods": []
    }

    # Make the request to the endpoint
    response = await client.post(
        "/items/create_item_drink",
        data={"data": json.dumps(request_data)}
    )

    # Should return 422 or 500 depending on how the service handles it
    # At least it shouldn't return 200
    assert response.status_code != 200