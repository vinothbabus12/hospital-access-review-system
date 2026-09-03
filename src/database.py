import os
import sqlite3
import pandas as pd

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "hospital_access.db")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def create_database(db_path=DB_PATH):
    """
    Ensures the database directory exists and returns an active SQLite connection.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_connection(db_path=DB_PATH):
    """
    Alias for create_database() to maintain backwards compatibility.
    """
    return create_database(db_path=db_path)


def create_tables(conn=None):
    """
    Creates the required database tables: users, entitlements, usage_events,
    review_decisions, and audit_log.
    """
    close_at_end = False
    if conn is None:
        conn = get_db_connection()
        close_at_end = True

    cursor = conn.cursor()

    # 1. users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        staff_type TEXT NOT NULL,
        manager TEXT,
        status TEXT NOT NULL,
        join_date TEXT NOT NULL
    );
    """)

    # 2. entitlements table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entitlements (
        entitlement_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        application TEXT NOT NULL,
        permission TEXT NOT NULL,
        granted_date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)

    # 3. usage_events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usage_events (
        event_id TEXT,
        user_id TEXT,
        application TEXT,
        action TEXT,
        event_timestamp TEXT,
        received_timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)

    # 4. review_decisions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS review_decisions (
        decision_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        entitlement_id TEXT NOT NULL,
        risk_score INTEGER NOT NULL,
        recommendation TEXT NOT NULL,
        reviewer_decision TEXT NOT NULL,
        override INTEGER NOT NULL,
        reason TEXT NOT NULL,
        reviewer TEXT NOT NULL,
        decision_timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (entitlement_id) REFERENCES entitlements(entitlement_id)
    );
    """)

    # 5. audit_log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        decision_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        entitlement_id TEXT NOT NULL,
        risk_score INTEGER DEFAULT 0,
        system_recommendation TEXT NOT NULL,
        reviewer_decision TEXT NOT NULL,
        override INTEGER NOT NULL,
        reason TEXT NOT NULL,
        reviewer TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    conn.commit()
    if close_at_end:
        conn.close()


def init_db():
    """
    Initializes database tables. Alias for create_tables().
    """
    create_tables()


def load_csv_data(data_dir=DATA_DIR):
    """
    Loads CSV data files from data_dir into their respective database tables.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop existing tables to ensure clean schema with PRIMARY KEY constraints
    for table in ["review_decisions", "usage_events", "entitlements", "users", "audit_log"]:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()

    create_tables(conn=conn)

    table_files = [
        ("users", "users.csv"),
        ("entitlements", "entitlements.csv"),
        ("usage_events", "usage_events.csv"),
        ("review_decisions", "review_decisions.csv"),
    ]

    for table_name, csv_filename in table_files:
        csv_path = os.path.join(data_dir, csv_filename)
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if table_name == "review_decisions" and "override" in df.columns:
                df["override"] = df["override"].astype(int)
            df.to_sql(table_name, conn, if_exists="append", index=False)
            conn.commit()

    conn.close()


def load_csv_data_to_db(data_dir=DATA_DIR):
    """
    Alias for load_csv_data() for backwards compatibility.
    """
    load_csv_data(data_dir=data_dir)


def retrieve_users():
    """
    Retrieves all records from the users table.
    """
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()
    return df


def get_users():
    return retrieve_users()


def retrieve_entitlements():
    """
    Retrieves all records from the entitlements table.
    """
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM entitlements", conn)
    conn.close()
    return df


def get_entitlements():
    return retrieve_entitlements()


def retrieve_usage_events():
    """
    Retrieves all records from the usage_events table.
    """
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM usage_events", conn)
    conn.close()
    return df


def get_usage_events():
    return retrieve_usage_events()


def save_review_decision(decision_data):
    """
    Saves a single review decision record to the review_decisions table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if isinstance(decision_data, dict):
        row = decision_data
    else:
        row = decision_data.to_dict()

    cursor.execute("""
    INSERT INTO review_decisions (
        decision_id, user_id, entitlement_id, risk_score, recommendation,
        reviewer_decision, override, reason, reviewer, decision_timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(decision_id) DO UPDATE SET
        user_id=excluded.user_id,
        entitlement_id=excluded.entitlement_id,
        risk_score=excluded.risk_score,
        recommendation=excluded.recommendation,
        reviewer_decision=excluded.reviewer_decision,
        override=excluded.override,
        reason=excluded.reason,
        reviewer=excluded.reviewer,
        decision_timestamp=excluded.decision_timestamp
    """, (
        str(row["decision_id"]),
        str(row["user_id"]),
        str(row["entitlement_id"]),
        int(row.get("risk_score", 0)),
        str(row.get("recommendation", "")),
        str(row.get("reviewer_decision", "")),
        int(row.get("override", 0)),
        str(row.get("reason", "")),
        str(row.get("reviewer", "")),
        str(row.get("decision_timestamp", ""))
    ))

    conn.commit()
    conn.close()


def save_review_decisions(decisions):
    """
    Saves a list of review decisions or DataFrame into the review_decisions table.
    """
    if isinstance(decisions, pd.DataFrame):
        records = decisions.to_dict("records")
    else:
        records = decisions
    for rec in records:
        save_review_decision(rec)


def retrieve_review_decisions():
    """
    Retrieves all records from the review_decisions table.
    """
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM review_decisions", conn)
    conn.close()
    return df


def retrieve_audit_decisions():
    """
    Alias for retrieve_review_decisions() to retrieve audit/review decisions.
    """
    return retrieve_review_decisions()


def get_review_decisions():
    return retrieve_review_decisions()


def execute_query(query, params=()):
    """
    Executes a SQL query and returns the results as a pandas DataFrame.
    """
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute_non_query(query, params=()):
    """
    Executes a non-query SQL command (INSERT, UPDATE, DELETE).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    load_csv_data()
    print("Database initialized and populated successfully at:", DB_PATH)

