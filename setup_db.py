"""
Script para configurar la base de datos SQLite para el Poker Tracker.
Crea las tablas: players, clubs, records
"""
import sqlite3
import os

DATABASE_PATH = "poker_tracker.db"

def create_database():
    """
    Crea la base de datos y las tablas necesarias.
    """
    # Eliminar base de datos existente si existe
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"🗑️  Base de datos anterior eliminada: {DATABASE_PATH}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Tabla de jugadores
    cursor.execute("""
        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            real_name TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Tabla 'players' creada")
    
    # Tabla de clubes
    cursor.execute("""
        CREATE TABLE clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Tabla 'clubs' creada")
    
    # Tabla de registros (records)
    cursor.execute("""
        CREATE TABLE records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER DEFAULT 2025,
            week TEXT NOT NULL,
            player_id INTEGER,
            club_id INTEGER NOT NULL,
            raw_nickname TEXT NOT NULL,
            profit REAL DEFAULT 0,
            rake REAL DEFAULT 0,
            total REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id),
            FOREIGN KEY (club_id) REFERENCES clubs(id)
        )
    """)
    print("✅ Tabla 'records' creada")

    # Tabla de deals de backing
    cursor.execute("""
        CREATE TABLE backing_deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            deal_percentage REAL NOT NULL,
            makeup_balance REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id)
        )
    """)
    print("✅ Tabla 'backing_deals' creada")
    
    # Tabla de mapeo de nicknames (auxiliar)
    cursor.execute("""
        CREATE TABLE nickname_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_nick TEXT NOT NULL,
            player_id INTEGER,
            club_id INTEGER,
            FOREIGN KEY (player_id) REFERENCES players(id),
            FOREIGN KEY (club_id) REFERENCES clubs(id),
            UNIQUE(original_nick, club_id)
        )
    """)
    print("✅ Tabla 'nickname_mappings' creada")
    
    # Crear índices para optimizar consultas
    cursor.execute("CREATE INDEX idx_records_player ON records(player_id)")
    cursor.execute("CREATE INDEX idx_records_club ON records(club_id)")
    cursor.execute("CREATE INDEX idx_records_week ON records(week)")
    cursor.execute("CREATE INDEX idx_nickname_mappings_nick ON nickname_mappings(original_nick)")
    print("✅ Índices creados")
    
    # Tabla de configuración de la app
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    print("✅ Tabla 'app_config' creada")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Base de datos creada exitosamente: {DATABASE_PATH}")
    return DATABASE_PATH


def verify_database():
    """
    Verifica que la base de datos se creó correctamente.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Listar todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("\n📋 Tablas en la base de datos:")
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"\n   📊 {table[0]}:")
        for col in columns:
            print(f"      - {col[1]} ({col[2]})")
    
    conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURACIÓN DE BASE DE DATOS - POKER TRACKER")
    print("=" * 60)
    
    create_database()
    verify_database()
