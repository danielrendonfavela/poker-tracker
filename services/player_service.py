import pandas as pd
import sqlite3
from services.database import get_connection

def load_players():
    """Carga todos los jugadores de la base de datos."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM players ORDER BY real_name", conn)
    conn.close()
    return df

def load_player_summary():
    """Carga resumen de ganancias por jugador."""
    conn = get_connection()
    query = """
        SELECT 
            COALESCE(p.real_name, 'Sin asignar') as jugador,
            COUNT(r.id) as partidas,
            COALESCE(SUM(r.profit), 0) as profit_total,
            COALESCE(SUM(r.rake), 0) as rake_total,
            COALESCE(SUM(r.total), 0) as balance_total,
            COUNT(DISTINCT r.club_id) as clubes
        FROM records r
        LEFT JOIN players p ON r.player_id = p.id
        GROUP BY p.id, p.real_name
        ORDER BY profit_total DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def load_player_nicknames():
    """Carga jugadores con sus nicknames."""
    conn = get_connection()
    query = """
        SELECT 
            p.real_name as nombre_real,
            GROUP_CONCAT(DISTINCT nm.original_nick) as nicknames,
            COUNT(DISTINCT nm.original_nick) as num_nicknames,
            GROUP_CONCAT(DISTINCT c.club_name) as clubes,
            COUNT(DISTINCT c.id) as num_clubes
        FROM players p
        LEFT JOIN nickname_mappings nm ON p.id = nm.player_id
        LEFT JOIN clubs c ON nm.club_id = c.id
        GROUP BY p.id, p.real_name
        ORDER BY p.real_name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_player(real_name: str, status: str = "active"):
    """Agrega un nuevo jugador a la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO players (real_name, status) VALUES (?, ?)",
            (real_name, status)
        )
        conn.commit()
        player_id = cursor.lastrowid
        return True, f"Jugador '{real_name}' agregado exitosamente (ID: {player_id})", player_id
    except sqlite3.IntegrityError:
        # Obtener el ID existente
        cursor.execute("SELECT id FROM players WHERE real_name = ?", (real_name,))
        row = cursor.fetchone()
        player_id = row[0] if row else None
        return False, f"El jugador '{real_name}' ya existe", player_id
    finally:
        conn.close()

def get_player_by_name(name: str):
    """Busca un jugador por nombre (exacto o parcial)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, real_name FROM players WHERE LOWER(real_name) = LOWER(?)",
        (name,)
    )
    row = cursor.fetchone()
    conn.close()
    return row

def get_all_players_dict():
    """Obtiene un diccionario de todos los jugadores {nombre: id}."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, real_name FROM players ORDER BY real_name")
    players = {row[1]: row[0] for row in cursor.fetchall()}
    conn.close()
    return players

def add_nickname_mapping(nickname: str, player_id: int, club_id: int):
    """Agrega un mapeo de nickname a jugador."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO nickname_mappings (original_nick, player_id, club_id) VALUES (?, ?, ?)",
            (nickname, player_id, club_id)
        )
        conn.commit()
        return True, "Nickname mapeado exitosamente"
    except sqlite3.IntegrityError:
        return False, "El nickname ya está mapeado para este club"
    finally:
        conn.close()
