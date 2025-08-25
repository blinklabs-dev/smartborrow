import snowflake.connector
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core.encryption_service import encrypt_password, decrypt_password

def get_connection_by_user_id(db: Session, user_id: int):
    """
    Retrieves the first snowflake connection for a given user.
    Note: For simplicity, this MVP assumes one connection per user.
    """
    return db.query(models.snowflake_connection.SnowflakeConnection).filter(models.snowflake_connection.SnowflakeConnection.owner_id == user_id).first()

def create_or_update_connection(db: Session, conn_in: schemas.SnowflakeConnectionCreate, user_id: int):
    """
    Creates a new snowflake connection for a user or updates the existing one.
    """
    encrypted_pass = encrypt_password(conn_in.password)

    existing_conn = get_connection_by_user_id(db, user_id=user_id)

    if existing_conn:
        # Update existing connection
        existing_conn.account_name = conn_in.account_name
        existing_conn.username = conn_in.username
        existing_conn.encrypted_password = encrypted_pass
        existing_conn.role = conn_in.role
        existing_conn.warehouse = conn_in.warehouse
    else:
        # Create new connection
        db_conn = models.snowflake_connection.SnowflakeConnection(
            account_name=conn_in.account_name,
            username=conn_in.username,
            encrypted_password=encrypted_pass,
            role=conn_in.role,
            warehouse=conn_in.warehouse,
            owner_id=user_id
        )
        db.add(db_conn)

    db.commit()
    # To get the updated/new object back, we query it again
    return get_connection_by_user_id(db, user_id=user_id)

def get_snowflake_connector(db: Session, user_id: int):
    """
    Creates and returns a live Snowflake connector for a given user.
    """
    conn_details = get_connection_by_user_id(db, user_id=user_id)

    if not conn_details:
        return None

    decrypted_password = decrypt_password(conn_details.encrypted_password)

    try:
        conn = snowflake.connector.connect(
            user=conn_details.username,
            password=decrypted_password,
            account=conn_details.account_name,
            role=conn_details.role,
            warehouse=conn_details.warehouse
        )
        return conn
    except snowflake.connector.errors.Error as e:
        # In a real app, you'd want to handle this error gracefully
        print(f"Error connecting to Snowflake: {e}")
        return None
