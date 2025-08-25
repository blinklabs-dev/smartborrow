import json
import sys
import os
from datetime import datetime

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.core.database import SessionLocal, engine, Base
from src.app.models.optimization_check import OptimizationCheck

# The JSON data provided by the user
JSON_DATA = """
{"id": "enable-auto-suspend-on-idle-warehouses", "slug": "enable-auto-suspend-on-idle-warehouses", "title": "Enable Auto-Suspend on Idle Warehouses", "category": "warehouse", "subcategory": "autosuspend", "impact_level": "quick_win", "complexity": "low", "estimated_savings_pct": 19, "effort_minutes": 15, "prerequisites": ["Role: ACCOUNTADMIN", "Access to QUERY_HISTORY"], "tags": ["warehouse", "autosuspend", "cost_optimization"], "last_reviewed": "2025-08-08", "status": "active", "version": 1, "description": "Idle dev and QA warehouses often burn credits even when no queries run. Auto-Suspend pauses compute after a short gap and eliminates that waste.", "how_to_implement": ["Run the SQL below to find the median idle gap (30-day window).", "Multiply that gap by 1.5 and round to the nearest 10 seconds.", "ALTER WAREHOUSE <name> SET AUTO_SUSPEND = <timeout>.", "After one week, add 30 s if cold-start complaints rise."], "code_snippet": "```sql\\n-- Median idle gap (seconds)\\nSELECT APPROX_PERCENTILE(\\n  TIMESTAMPDIFF('second',\\n      LAG(start_time) OVER(PARTITION BY warehouse_name ORDER BY start_time),\\n      start_time),\\n  0.5) AS median_gap_sec\\nFROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY\\nWHERE warehouse_name = 'DEV_WH'\\n  AND start_time >= DATEADD(day,-30,CURRENT_TIMESTAMP());\\n\\n-- Apply 90-second auto-suspend\\nALTER WAREHOUSE DEV_WH SET AUTO_SUSPEND = 90;\\n```", "success_indicators": ["Warehouse credit burn \\u2193 \\u2265 20 %", "No rise in dashboard time-out complaints"], "when_to_use": "If the median idle gap is \\u2265 120 s for at least 70 % of queries."}
{"id": "right-size-warehouse-compute", "slug": "right-size-warehouse-compute", "title": "Right-Size Warehouse Compute", "category": "warehouse", "subcategory": "sizing", "impact_level": "high_impact", "complexity": "medium", "estimated_savings_pct": 25, "effort_minutes": 46, "prerequisites": ["Role: ACCOUNTADMIN", "Access to WAREHOUSE_LOAD_HISTORY"], "tags": ["warehouse", "sizing", "cost_optimization"], "last_reviewed": "2025-08-08", "status": "active", "version": 1, "description": "Many warehouses stay over-provisioned after launch. Adjusting size to match real workload trims credits without hurting performance.", "how_to_implement": ["Query WAREHOUSE_LOAD_HISTORY for average queue length and execution time.", "If queue \\u2248 0 and exec time \\u226a SLA \\u2192 scale down; if queue \\u2265 1 and exec time \\u226b SLA \\u2192 scale up.", "ALTER WAREHOUSE ... SET WAREHOUSE_SIZE = <new_size>.", "Re-check weekly until credits/query stabilise."], "code_snippet": "```sql\\n-- Avg queue length & exec time last 7 days\\nSELECT warehouse_name,\\n       AVG(queued_overload_time)/1000 AS avg_queue_s,\\n       AVG(execution_time)/1000 AS avg_exec_s\\nFROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY\\nWHERE start_time >= DATEADD(day,-7,CURRENT_TIMESTAMP())\\nGROUP BY 1;\\n```", "success_indicators": ["Credits/query \\u2193 \\u2265 25 %", "Query latency within SLA"], "when_to_use": "When avg queue length < 0.1 and avg exec time < 50 % of SLA."}
{"id": "convert-temp-staging-tables-to-transient", "slug": "convert-temp-staging-tables-to-transient", "title": "Convert Temp Staging Tables to Transient", "category": "storage", "subcategory": "transient_tables", "impact_level": "quick_win", "complexity": "low", "estimated_savings_pct": 13, "effort_minutes": 16, "prerequisites": ["Role: SYSADMIN"], "tags": ["storage", "transient_tables", "cost_optimization"], "last_reviewed": "2025-08-08", "status": "active", "version": 1, "description": "Transient tables skip seven-day Fail-Safe fees—ideal for ETL staging data you can recreate anytime.", "how_to_implement": ["Identify tables older than seven days with zero reads (ACCOUNT_USAGE.TABLE_STORAGE_METRICS).", "DROP and recreate them as CREATE TRANSIENT TABLE ... ;", "Add automatic DROP in your ETL job to keep storage minimal.", "Verify restore requirements are covered elsewhere."], "code_snippet": "```sql\\n-- Find cold staging tables\\nSELECT table_name, DATEDIFF(day, last_altered, CURRENT_DATE) AS days_old\\nFROM SNOWFLAKE.ACCOUNT_USAGE.TABLES\\nWHERE table_type='TEMPORARY'\\n  AND table_schema='STAGE'\\n  AND DATEDIFF(day, last_altered, CURRENT_DATE) > 7;\\n\\n-- Convert to transient\\nCREATE OR REPLACE TRANSIENT TABLE stage_customer AS\\nSELECT * FROM stage_customer_temp;\\n```", "success_indicators": ["Storage costs \\u2193 \\u2265 10 %", "No impact on downstream jobs"], "when_to_use": "For ETL scratch tables you can rebuild within 24 hours."}
"""

def load_knowledge_base():
    db = SessionLocal()

    # IDs for the MVP checks
    mvp_check_ids = [
        "enable-auto-suspend-on-idle-warehouses",
        "right-size-warehouse-compute",
        "convert-temp-staging-tables-to-transient"
    ]

    # The user provided a string with one JSON object per line.
    # We can split the string by lines and parse each line as a separate JSON object.
    lines = JSON_DATA.strip().splitlines()

    try:
        for line in lines:
            check_data = json.loads(line)
            if check_data['id'] in mvp_check_ids:
                # Check if it already exists
                exists = db.query(OptimizationCheck).filter(OptimizationCheck.id == check_data['id']).first()
                if not exists:
                    # Convert date string to date object
                    check_data['last_reviewed'] = datetime.strptime(check_data['last_reviewed'], '%Y-%m-%d').date()

                    # Ensure float conversion for savings_pct
                    if check_data.get('estimated_savings_pct'):
                        check_data['estimated_savings_pct'] = float(check_data['estimated_savings_pct'])

                    # Convert lists to JSON strings for DB storage
                    for key in ['prerequisites', 'tags', 'how_to_implement', 'success_indicators']:
                        if key in check_data and isinstance(check_data[key], list):
                            check_data[key] = json.dumps(check_data[key])

                    new_check = OptimizationCheck(**check_data)
                    db.add(new_check)

        db.commit()
        print("Successfully loaded MVP knowledge base checks.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Loading knowledge base...")
    # This ensures tables are created before we try to load data
    Base.metadata.create_all(bind=engine)
    load_knowledge_base()
