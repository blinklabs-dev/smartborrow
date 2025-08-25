import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.services import scanner_service, risk_assessor_service, executor_service, snowflake_service
from app.schemas import SnowflakeConnectionCreate
from app.models.user import User
from app.scripts.load_kb import load_knowledge_base

# Fixtures are auto-loaded from conftest.py

def test_scanner_finds_issue(db_session: Session, test_user: User):
    # Setup: Load KB and create a snowflake connection for the user
    load_knowledge_base(db=db_session)
    conn_in = SnowflakeConnectionCreate(account_name="test", username="test", password="test")
    snowflake_service.create_or_update_connection(db=db_session, conn_in=conn_in, user_id=test_user.id)

    # Mock the snowflake connector
    mock_cursor = MagicMock()
    # This specific query from the knowledge base is what we expect to run
    # We will return a result for it.
    mock_cursor.fetchall.return_value = [("DEV_WH",)]
    mock_cursor.description = [("WAREHOUSE_NAME",)]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch('app.services.snowflake_service.get_snowflake_connector', return_value=mock_conn):
        findings = scanner_service.run_scan(db=db_session, user_id=test_user.id)

        assert isinstance(findings, list)
        assert len(findings) > 0
        assert any(f['check_id'] == 'enable-auto-suspend-on-idle-warehouses' for f in findings)

def test_risk_assessor_classifies_risk(db_session: Session):
    # Load the KB so the service can find the check
    load_knowledge_base(db=db_session)

    finding = { "check_id": "enable-auto-suspend-on-idle-warehouses" }
    risk = risk_assessor_service.assess_risk_of_finding(db=db_session, finding=finding)
    assert risk == "LOW"

    finding_high_risk = { "check_id": "right-size-warehouse-compute" }
    risk_high = risk_assessor_service.assess_risk_of_finding(db=db_session, finding=finding_high_risk)
    assert risk_high == "MEDIUM"

def test_executor_applies_fix(db_session: Session, test_user: User):
    # Load the KB and create a connection
    load_knowledge_base(db=db_session)
    conn_in = SnowflakeConnectionCreate(account_name="test", username="test", password="test")
    snowflake_service.create_or_update_connection(db=db_session, conn_in=conn_in, user_id=test_user.id)

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch('app.services.snowflake_service.get_snowflake_connector', return_value=mock_conn):
        result = executor_service.execute_fix(db=db_session, user_id=test_user.id, check_id="enable-auto-suspend-on-idle-warehouses")

        assert result["status"] == "success"

        # Check that the execute method was called with the correct ALTER WAREHOUSE command
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "ALTER WAREHOUSE DEV_WH SET AUTO_SUSPEND = 90" in executed_sql
