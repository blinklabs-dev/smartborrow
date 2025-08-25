import json
from sqlalchemy.orm import Session
from .. import models, schemas
from . import snowflake_service

def run_scan(db: Session, user_id: int):
    """
    Runs all enabled optimization checks for a given user.
    """
    findings = []

    # 1. Get a live Snowflake connection
    conn = snowflake_service.get_snowflake_connector(db=db, user_id=user_id)
    if not conn:
        # Could raise an exception or return a status
        return {"error": "Could not connect to Snowflake."}

    cursor = conn.cursor()

    # 2. Get all enabled checks from our knowledge base
    checks = db.query(models.optimization_check.OptimizationCheck).filter(models.optimization_check.OptimizationCheck.status == 'active').all()

    # 3. Loop through each check and execute its detection SQL
    for check in checks:
        try:
            # For simplicity, we're executing the first SQL statement in the snippet.
            # A more robust version would parse this properly.
            sql_statement = check.code_snippet.split(';')[0].strip()

            # A real implementation would need to substitute placeholders,
            # e.g., for warehouse names or other parameters.
            # For this MVP, we'll run it as is.
            cursor.execute(sql_statement)
            results = cursor.fetchall()

            # 4. If the query returns results, an issue is found.
            if results:
                # Get column names from cursor.description
                column_names = [desc[0] for desc in cursor.description]

                # Format results into a list of dicts
                formatted_results = []
                for row in results:
                    formatted_results.append(dict(zip(column_names, row)))

                finding = {
                    "check_id": check.id,
                    "title": check.title,
                    "description": check.description,
                    "query_results": formatted_results,
                    "details": f"Found {len(results)} potential issue(s)."
                }
                findings.append(finding)

        except Exception as e:
            # Log the error and continue to the next check
            print(f"Error running check '{check.id}': {e}")
            continue

    cursor.close()
    conn.close()

    return findings
