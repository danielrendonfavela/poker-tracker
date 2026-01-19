import pandas as pd
from services.database import get_connection

def load_clubs():
    """Carga todos los clubes de la base de datos."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM clubs ORDER BY club_name", conn)
    conn.close()
    return df

def load_club_summary():
    """Carga resumen de ganancias por club."""
    conn = get_connection()
    query = """
        SELECT 
            c.club_name as club,
            COUNT(r.id) as registros,
            COUNT(DISTINCT r.player_id) as jugadores,
            COUNT(DISTINCT r.week) as semanas,
            COALESCE(SUM(r.profit), 0) as profit_total,
            COALESCE(SUM(r.rake), 0) as rake_total,
            COALESCE(SUM(r.total), 0) as balance_total
        FROM records r
        JOIN clubs c ON r.club_id = c.id
        GROUP BY c.id, c.club_name
        ORDER BY profit_total DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_club_id(club_name: str):
    """Obtiene el ID de un club por nombre."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clubs WHERE club_name = ?", (club_name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def load_nickname_count():
    """Cuenta el número total de nicknames únicos en la DB."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT original_nick) FROM nickname_mappings")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_clubs_summary():
    """Retorna una lista simple de diccionarios con id y nombre del club."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, club_name FROM clubs ORDER BY club_name")
    rows = cursor.fetchall()
    conn.close()
    
    return [{'id': row[0], 'name': row[1]} for row in rows]
