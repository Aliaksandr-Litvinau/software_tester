import uuid
from unittest.mock import MagicMock

import pytest
from lamb.db import DeclarativeBase
from lamb.exc import InvalidParamValueError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.models import AbstractUser, ExchangeRatesRecord, RefreshToken, SuperAdmin, UserType, Operator


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("postgresql://app_user:password@localhost/app_core")
    DeclarativeBase.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    session = session()
    yield session
    session.close()


def test_abstract_user_set_password(db_session, mocker):
    user = AbstractUser()
    mocker.patch('api.models.validate_password')
    user.set_password("password123")
    assert user.password_hash is not None


def test_abstract_user_check_password(db_session, mocker):
    user = AbstractUser()
    mocker.patch('api.models.validate_password')
    user.set_password("password123")
    assert user.check_password("password123") is True
    assert user.check_password("wrongpassword") is False


def test_abstract_user_change_password(db_session, mocker):
    user = AbstractUser()
    mocker.patch('api.models.validate_password')
    user.set_password("password123")
    user.change_password("password123", "newpassword")
    assert user.check_password("newpassword") is True


def test_abstract_user_validate_name(db_session):
    with pytest.raises(InvalidParamValueError):
        user = AbstractUser(email="invalid_email")
        db_session.add(user)
        db_session.commit()


def test_super_admin_can_create_user(db_session):
    super_admin = SuperAdmin(is_confirmed=True)
    assert super_admin.can_create_user(UserType.USER) is True
    assert super_admin.can_create_user(UserType.SUPER_ADMIN) is False


def test_super_admin_can_read_user(db_session):
    super_admin = SuperAdmin(is_confirmed=True)
    user = AbstractUser()
    assert super_admin.can_read_user(user) is True


def test_super_admin_can_edit_user(db_session):
    super_admin = SuperAdmin(is_confirmed=True)
    user = AbstractUser()
    assert super_admin.can_edit_user(user) is True


def test_operator_can_create_user(db_session):
    operator = Operator(is_confirmed=True)
    assert operator.can_create_user(UserType.USER) is False


def test_operator_can_read_user(db_session):
    operator = Operator(is_confirmed=True)
    user = AbstractUser()
    assert operator.can_read_user(user) is False
    assert operator.can_read_user(operator) is True


def test_operator_can_edit_user(db_session):
    operator = Operator(is_confirmed=True)
    user = AbstractUser()
    assert operator.can_edit_user(user) is False
    assert operator.can_edit_user(operator) is True


def test_refresh_token_creation(db_session, mocker):
    # create a mock for a function that returns a UUID
    mock_uuid = uuid.uuid4()  # here you can specify any UUID value for the test

    with mocker.patch('api.models.uuid.uuid4', return_value=mock_uuid):
        # creating a RefreshToken using the mock uuid.uuid4 function
        user_id = uuid.uuid4()
        refresh_token = RefreshToken(value="token123", user_id=user_id)

        # Проверяем, что значения корректно установлены
        assert refresh_token.value == "token123"
        assert refresh_token.user_id == user_id
        assert refresh_token.user_id is not None


def test_exchange_rates_record_creation(db_session):
    user = AbstractUser()
    db_session.add(user)  # Add the user to the session
    db_session.flush()  # Flush the session to assign a user_id to the user

    exchange_rate = ExchangeRatesRecord(actor_id=user.user_id, rate=1.5)
    db_session.add(exchange_rate)
    db_session.commit()

    assert exchange_rate.actor_id == user.user_id
    assert exchange_rate.rate == 1.5
    assert exchange_rate.rate != 3.0

