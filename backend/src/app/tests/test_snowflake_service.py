from unittest.mock import patch
from sqlalchemy.orm import Session

from app.services import snowflake_service
from app.schemas import SnowflakeConnectionCreate
from app.core.encryption_service import decrypt_password
from app.models.user import User

def test_create_snowflake_connection(db_session: Session, test_user: User):
    conn_in = SnowflakeConnectionCreate(
        account_name="test_account",
        username="test_user",
        password="snowflake_password",
        role="SYSADMIN",
        warehouse="COMPUTE_WH"
    )

    # Create the connection
    db_conn = snowflake_service.create_or_update_connection(db=db_session, conn_in=conn_in, user_id=test_user.id)

    assert db_conn is not None
    assert db_conn.owner_id == test_user.id
    assert db_conn.account_name == "test_account"

    # Verify the password was encrypted
    assert db_conn.encrypted_password != conn_in.password.encode()

    # Verify we can decrypt it back to the original
    decrypted_pass = decrypt_password(db_conn.encrypted_password)
    assert decrypted_pass == conn_in.password

def test_update_snowflake_connection(db_session: Session, test_user: User):
    # Create initial connection
    conn_in_1 = SnowflakeConnectionCreate(
        account_name="account_v1", username="user_v1", password="password_v1"
    )
    snowflake_service.create_or_update_connection(db=db_session, conn_in=conn_in_1, user_id=test_user.id)

    # Update it
    conn_in_2 = SnowflakeConnectionCreate(
        account_name="account_v2", username="user_v2", password="password_v2"
    )
    updated_conn = snowflake_service.create_or_update_connection(db=db_session, conn_in=conn_in_2, user_id=test_user.id)

    assert updated_conn.account_name == "account_v2"
    decrypted_pass = decrypt_password(updated_conn.encrypted_password)
    assert decrypted_pass == "password_v2"

@patch('snowflake.connector.connect')
def test_get_snowflake_connector(mock_snowflake_connect, db_session: Session, test_user: User):
    """
    Tests that the service attempts to connect to snowflake with the correct,
    decrypted credentials.
    """
    mock_snowflake_connect.return_value = "Success" # Mock the return value

    conn_in = SnowflakeConnectionCreate(
        account_name="test_account",
        username="test_user",
        password="my_secret_password",
        role="SYSADMIN",
        warehouse="COMPUTE_WH"
    )
    snowflake_service.create_or_update_connection(db=db_session, conn_in=conn_in, user_id=test_user.id)

    # Attempt to get a connector
    connector = snowflake_service.get_snowflake_connector(db=db_session, user_id=test_user.id)

    assert connector == "Success"

    # Check that the snowflake.connector.connect function was called with the decrypted password
    mock_snowflake_connect.assert_called_once_with(
        user="test_user",
        password="my_secret_password", # The plain text password
        account="test_account",
        role="SYSADMIN",
        warehouse="COMPUTE_WH"
    )
