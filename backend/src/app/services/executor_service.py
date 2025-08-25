from sqlalchemy.orm import Session
from .. import models
from . import snowflake_service
import re

def execute_fix(db: Session, user_id: int, check_id: str):
    """
    Executes the fix for a given optimization check.
    """

    check = db.query(models.optimization_check.OptimizationCheck).filter(models.optimization_check.OptimizationCheck.id == check_id).first()
    if not check:
        return {"status": "error", "message": "Check not found."}

    conn = snowflake_service.get_snowflake_connector(db=db, user_id=user_id)
    if not conn:
        return {"status": "error", "message": "Could not connect to Snowflake."}

    cursor = conn.cursor()

    try:
        # This is a simplified and potentially fragile way to extract the fix SQL.
        # A more robust solution would have a dedicated 'fix_sql' field in the model.
        # We look for commands like ALTER, CREATE, DROP, etc.

        fix_commands = []
        # A simple regex to find SQL commands. We look for a complete command ending in a semicolon.
        # We find all matches and typically expect the second one to be the "fix" command in our KB.
        all_commands = re.findall(r"([^;]+;)", check.code_snippet, re.DOTALL)

        # Heuristic: The "fix" command is often the second one in the snippet.
        # This is fragile and should be improved with a better KB structure.
        if len(all_commands) < 2:
            return {"status": "error", "message": "Could not extract a fix command from snippet."}

        # The command to execute is the second one, stripped of whitespace.
        command_to_execute = all_commands[1].strip()

        # In a real app, we would need to substitute placeholders here.
        # e.g., replace <name> with the actual warehouse name from the scanner's findings.
        # For the MVP, we assume the command is ready to run.
        print(f"Executing command: {command_to_execute}")
        cursor.execute(command_to_execute)

        return {"status": "success", "message": f"Successfully applied fix for '{check.title}'."}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()
