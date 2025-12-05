"""Migration script to add fight result tables and resolution fields."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "mma_data.db"

def migrate():
    """Add new tables and columns for fight results and resolution tracking."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Starting database migration...")
    
    try:
        # 1. Add resolution fields to predictions table
        print("\n1. Adding resolution fields to predictions table...")
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN is_correct INTEGER DEFAULT NULL")
            print("   ✓ Added is_correct column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⊙ is_correct column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN resolved_at TIMESTAMP DEFAULT NULL")
            print("   ✓ Added resolved_at column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⊙ resolved_at column already exists")
            else:
                raise
        
        # 2. Add resolution fields to scorecards table
        print("\n2. Adding resolution fields to scorecards table...")
        try:
            cursor.execute("ALTER TABLE scorecards ADD COLUMN correct_rounds INTEGER DEFAULT 0")
            print("   ✓ Added correct_rounds column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⊙ correct_rounds column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE scorecards ADD COLUMN total_rounds INTEGER DEFAULT 0")
            print("   ✓ Added total_rounds column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⊙ total_rounds column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE scorecards ADD COLUMN resolved_at TIMESTAMP DEFAULT NULL")
            print("   ✓ Added resolved_at column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⊙ resolved_at column already exists")
            else:
                raise
        
        # 3. Add resolution field to round_scores table
        print("\n3. Adding resolution field to round_scores table...")
        try:
            cursor.execute("ALTER TABLE round_scores ADD COLUMN is_correct INTEGER DEFAULT NULL")
            print("   ✓ Added is_correct column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⊙ is_correct column already exists")
            else:
                raise
        
        # 4. Create fight_results table
        print("\n4. Creating fight_results table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fight_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fight_id INTEGER NOT NULL UNIQUE,
                winner VARCHAR(20) NOT NULL,
                method VARCHAR(20) NOT NULL,
                finish_round INTEGER,
                finish_time VARCHAR(10),
                is_resolved INTEGER DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fight_id) REFERENCES fights(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fight_result_fight ON fight_results(fight_id)")
        print("   ✓ Created fight_results table")
        
        # 5. Create official_scorecards table
        print("\n5. Creating official_scorecards table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS official_scorecards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fight_result_id INTEGER NOT NULL,
                judge_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fight_result_id) REFERENCES fight_results(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_official_scorecard_result ON official_scorecards(fight_result_id)")
        print("   ✓ Created official_scorecards table")
        
        # 6. Create official_round_scores table
        print("\n6. Creating official_round_scores table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS official_round_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                official_scorecard_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                fighter1_score INTEGER NOT NULL,
                fighter2_score INTEGER NOT NULL,
                FOREIGN KEY (official_scorecard_id) REFERENCES official_scorecards(id) ON DELETE CASCADE,
                UNIQUE (official_scorecard_id, round_number)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_official_roundscore_scorecard ON official_round_scores(official_scorecard_id)")
        print("   ✓ Created official_round_scores table")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Show summary
        print("\n📊 Database Summary:")
        cursor.execute("SELECT COUNT(*) FROM predictions")
        print(f"   Predictions: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM scorecards")
        print(f"   Scorecards: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM fight_results")
        print(f"   Fight Results: {cursor.fetchone()[0]}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

