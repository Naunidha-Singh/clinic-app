"""
Database initialization and connection helper for the Clinic Management System.
Uses PostgreSQL with psycopg2 driver.

─── Transactions & Isolation Levels ───────────────────────────────────────────
PostgreSQL supports four standard SQL isolation levels:
  1. READ UNCOMMITTED — allows dirty reads (PostgreSQL treats as READ COMMITTED)
  2. READ COMMITTED   — only reads committed data; releases read locks immediately
  3. REPEATABLE READ  — guarantees repeatable reads within a transaction
  4. SERIALIZABLE     — strongest: locks sets of objects, prevents phantom reads

We use READ COMMITTED (PostgreSQL's default) for most operations because:
  - It prevents dirty reads (never see uncommitted data from other transactions)
  - It allows higher concurrency than SERIALIZABLE (read locks released immediately)
  - For a clinic management system, slight non-repeatable reads are acceptable
    since data is typically accessed by one user at a time

For the transfer_appointments endpoint, we use SERIALIZABLE isolation to ensure
that the multi-row UPDATE is fully isolated — no other transaction can modify
the appointment records mid-transfer.

Reference: TransactionsConcurrency_slides.pdf — ACID properties, S2PL,
isolation levels (slides 45-55), consistency vs. concurrency tradeoff (slide 56-57)
"""

import psycopg2
import psycopg2.extras
import os

# PostgreSQL connection parameters
# Update these to match your local PostgreSQL configuration
DB_CONFIG = {
    'dbname': 'clinic_db',
    'user': 'postgres',
    'password': os.environ.get('PGPASSWORD', 'postgres'),  # Set via environment variable or change default
    'host': '127.0.0.1',
    'port': '5432',
}


def get_db():
    """Get a database connection with dict cursor enabled.

    Connection settings:
    - cursor_factory=RealDictCursor: Allows accessing columns by name (like sqlite3.Row).
    - autocommit=False: We explicitly manage transactions with BEGIN/COMMIT/ROLLBACK.
    - PostgreSQL enforces foreign keys by default (no PRAGMA needed).
    """
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False  # We manage transactions explicitly
    return conn


def init_db():
    """Initialize the database: create tables, indexes, and seed data if needed."""
    conn = get_db()
    conn.autocommit = True  # Schema DDL needs autocommit
    cur = conn.cursor()

    # Read and execute schema (includes CREATE TABLE and CREATE INDEX statements)
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema_path, 'r') as f:
        cur.execute(f.read())

    # Check if data already exists
    cur.execute("SELECT COUNT(*) FROM departments")
    count = cur.fetchone()[0]
    if count == 0:
        # Seed with sample data
        seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_data.sql')
        with open(seed_path, 'r') as f:
            cur.execute(f.read())
        print("✓ Database seeded with sample data.")
    else:
        print("✓ Database already contains data.")

    # Verify indexes were created
    cur.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename IN ('patients', 'doctors', 'appointments', 'prescriptions')
        AND indexname LIKE 'idx_%'
        ORDER BY indexname
    """)
    indexes = cur.fetchall()
    print(f"✓ {len(indexes)} custom indexes active:")
    for idx in indexes:
        idx_type = 'HASH' if 'USING hash' in idx[1] else 'BTREE'
        print(f"  - {idx[0]} ({idx_type})")

    # Verify stored procedures were created
    cur.execute("""
        SELECT proname FROM pg_proc
        WHERE proname LIKE 'sp_%'
        ORDER BY proname
    """)
    procs = cur.fetchall()
    print(f"✓ {len(procs)} stored procedures active:")
    for proc in procs:
        print(f"  - {proc[0]}")

    cur.close()
    conn.close()


if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
