"""
Additional tests for missing components in the application
"""
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.dependencies import get_current_user, get_current_active_user
from app.core.config.database.db_async import get_db
from app.auth.schemas import UserCreate
from unittest.mock import AsyncMock, MagicMock
import jwt


@pytest.mark.asyncio
async def test_user_authentication_flow(authenticated_client_with_db, test_db_session):
    """Test the complete user authentication flow"""
    # Create a user
    user_data = {
        "username": "auth_test_user",
        "email": "auth_test@example.com",
        "password": "securepassword123"
    }
    
    user_repo = UserRepository()
    created_user = await user_repo.create(user_data, test_db_session)
    
    # Verify user was created with hashed password
    assert created_user.username == "auth_test_user"
    assert created_user.email == "auth_test@example.com"
    assert hasattr(created_user, "hashed_password")
    assert created_user.hashed_password != "securepassword123"  # Should be hashed


@pytest.mark.asyncio
async def test_user_authentication_success(authenticated_client_with_db, test_db_session):
    """Test successful user authentication"""
    # Create a user
    user_data = {
        "username": "auth_success_user",
        "email": "auth_success@example.com",
        "password": "testpassword123"
    }
    
    user_repo = UserRepository()
    created_user = await user_repo.create(user_data, test_db_session)
    
    # Test authentication
    authenticated_user = await user_repo.authenticate(
        "auth_success_user", 
        "testpassword123", 
        test_db_session
    )
    
    assert authenticated_user is not None
    assert authenticated_user.id == created_user.id
    assert authenticated_user.username == "auth_success_user"


@pytest.mark.asyncio
async def test_user_authentication_failure(authenticated_client_with_db, test_db_session):
    """Test failed user authentication"""
    # Create a user
    user_data = {
        "username": "auth_fail_user",
        "email": "auth_fail@example.com",
        "password": "testpassword123"
    }
    
    user_repo = UserRepository()
    await user_repo.create(user_data, test_db_session)
    
    # Test authentication with wrong password
    authenticated_user = await user_repo.authenticate(
        "auth_fail_user", 
        "wrongpassword", 
        test_db_session
    )
    
    assert authenticated_user is None
    
    # Test authentication with wrong username
    authenticated_user = await user_repo.authenticate(
        "nonexistent_user", 
        "testpassword123", 
        test_db_session
    )
    
    assert authenticated_user is None


@pytest.mark.asyncio
async def test_password_hashing_functions(authenticated_client_with_db, test_db_session):
    """Test password wordhash and verification functions"""
    user_repo = UserRepository()
    
    # Test password wordhash
    plain_password = "testpassword123"
    hashed_password = user_repo.get_password_hash(plain_password)
    
    assert hashed_password is not None
    assert hashed_password != plain_password  # Should be different
    
    # Test password verification
    is_valid = user_repo.verify_password(plain_password, hashed_password)
    assert is_valid is True
    
    # Test invalid password verification
    is_invalid = user_repo.verify_password("wrongpassword", hashed_password)
    assert is_invalid is False


@pytest.mark.asyncio
async def test_repository_get_by_fields(authenticated_client_with_db, test_db_session):
    """Test the get_by_fields repository method"""
    user_data = {
        "username": "field_test_user",
        "email": "field_test@example.com",
        "password": "testpassword123"
    }
    
    user_repo = UserRepository()
    created_user = await user_repo.create(user_data, test_db_session)
    
    # Test getting user by username
    retrieved_user = await user_repo.get_by_fields(
        {"username": "field_test_user"}, 
        User, 
        test_db_session
    )
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == "field_test_user"
    
    # Test getting user by email
    retrieved_user = await user_repo.get_by_fields(
        {"email": "field_test@example.com"}, 
        User, 
        test_db_session
    )
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == "field_test@example.com"
    
    # Test getting non-existent user
    non_existent_user = await user_repo.get_by_fields(
        {"username": "nonexistent"}, 
        User, 
        test_db_session
    )
    
    assert non_existent_user is None


@pytest.mark.asyncio
async def test_repository_get_by_obj(authenticated_client_with_db, test_db_session):
    """Test the get_by_obj repository method"""
    user_data = {
        "username": "obj_test_user",
        "email": "obj_test@example.com",
        "password": "testpassword123"
    }
    
    user_repo = UserRepository()
    created_user = await user_repo.create(user_data, test_db_session)
    
    # Test getting user by username
    retrieved_user = await user_repo.get_by_obj(
        {"username": "obj_test_user"}, 
        User, 
        test_db_session
    )
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == "obj_test_user"


@pytest.mark.asyncio
async def test_repository_get_all_and_count(authenticated_client_with_db, test_db_session):
    """Test repository get_all and count methods"""
    user_repo = UserRepository()
    
    # Create multiple users
    users_data = [
        {"username": "user1", "email": "user1@example.com", "password": "password1"},
        {"username": "user2", "email": "user2@example.com", "password": "password2"},
        {"username": "user3", "email": "user3@example.com", "password": "password3"},
    ]
    
    created_users = []
    for user_data in users_data:
        user = await user_repo.create(user_data, test_db_session)
        created_users.append(user)
    
    # Test get_all_count
    count = await user_repo.get_all_count(User, test_db_session)
    assert count >= len(created_users)  # At least the users we created
    
    # Test get_count with a date (should include our users)
    from datetime import datetime
    count_with_date = await user_repo.get_count(datetime.min, User, test_db_session)
    assert count_with_date >= len(created_users)


@pytest.mark.asyncio
async def test_repository_patch_with_validation(authenticated_client_with_db, test_db_session):
    """Test repository patch method with validation"""
    user_data = {
        "username": "patch_test_user",
        "email": "patch_test@example.com",
        "password": "testpassword123"
    }
    
    user_repo = UserRepository()
    created_user = await user_repo.create(user_data, test_db_session)
    
    # Test updating user fields
    update_data = {
        "username": "updated_patch_user",
        "email": "updated@example.com"
    }
    
    updated_user = await user_repo.patch(created_user, update_data, test_db_session)
    
    assert updated_user.username == "updated_patch_user"
    assert updated_user.email == "updated@example.com"


def test_app_has_expected_attributes():
    """Test that the FastAPI app has expected configuration"""
    assert hasattr(app, 'title')
    assert hasattr(app, 'description')
    assert hasattr(app, 'version')
    assert isinstance(app, FastAPI)


@pytest.mark.asyncio
async def test_database_session_fixture_works(test_db_session):
    """Test that the database session fixture works correctly"""
    assert test_db_session is not None
    assert isinstance(test_db_session, AsyncSession)
    
    # Test that we can execute a simple query
    from sqlalchemy import text
    result = await test_db_session.execute(text("SELECT 1"))
    assert result is not None