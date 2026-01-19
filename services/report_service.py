import pandas as pd
import sqlite3
from services.database import get_connection

def load_records():
    """Carga todos los registros de la base de datos."""
    conn = get_connection()
    query = """
        SELECT 
            r.id,
            r.week,
            COALESCE(p.real_name, 'Sin asignar') as player,
            c.club_name as club,
            r.raw_nickname,
            r.profit,
            r.rake,
            r.total
        FROM records r
        LEFT JOIN players p ON r.player_id = p.id
        LEFT JOIN clubs c ON r.club_id = c.id
        ORDER BY r.week DESC, c.club_name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def load_week_count():
    """Cuenta el número de semanas únicas en la DB."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT week) FROM records")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def load_dashboard_stats():
    """Carga estadísticas para el dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Conteos
    cursor.execute("SELECT COUNT(*) FROM players")
    stats['players'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM clubs")
    stats['clubs'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM records")
    stats['records'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT original_nick) FROM nickname_mappings")
    stats['nicknames'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT week) FROM records")
    stats['weeks'] = cursor.fetchone()[0]
    
    # Totales financieros
    cursor.execute("SELECT COALESCE(SUM(profit), 0), COALESCE(SUM(rake), 0), COALESCE(SUM(total), 0) FROM records")
    result = cursor.fetchone()
    stats['total_profit'] = result[0]
    stats['total_rake'] = result[1]
    stats['total_balance'] = result[2]
    
    conn.close()
    return stats

def load_weekly_summary(club_name: str = None):
    """Carga resumen por semana, opcionalmente filtrado por club."""
    conn = get_connection()
    
    if club_name and club_name != "Todos":
        query = """
            SELECT 
                r.week as semana,
                c.club_name as club,
                COUNT(r.id) as registros,
                COUNT(DISTINCT r.player_id) as jugadores,
                COALESCE(SUM(r.profit), 0) as profit_total,
                COALESCE(SUM(r.rake), 0) as rake_total,
                COALESCE(SUM(r.total), 0) as balance_total
            FROM records r
            JOIN clubs c ON r.club_id = c.id
            WHERE c.club_name = ?
            GROUP BY r.week, c.club_name
            ORDER BY r.week DESC
        """
        df = pd.read_sql_query(query, conn, params=[club_name])
    else:
        query = """
            SELECT 
                r.week as semana,
                c.club_name as club,
                COUNT(r.id) as registros,
                COUNT(DISTINCT r.player_id) as jugadores,
                COALESCE(SUM(r.profit), 0) as profit_total,
                COALESCE(SUM(r.rake), 0) as rake_total,
                COALESCE(SUM(r.total), 0) as balance_total
            FROM records r
            JOIN clubs c ON r.club_id = c.id
            GROUP BY r.week, c.club_name
            ORDER BY c.club_name, r.week DESC
        """
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df

def load_week_details(week: str, club_name: str = None):
    """Carga los registros detallados de una semana específica."""
    conn = get_connection()
    
    if club_name and club_name != "Todos":
        query = """
            SELECT 
                r.year as año,
                r.week as semana,
                c.club_name as club,
                COALESCE(p.real_name, 'Sin asignar') as jugador,
                r.raw_nickname as nickname,
                r.profit,
                r.rake,
                r.total as balance
            FROM records r
            LEFT JOIN players p ON r.player_id = p.id
            JOIN clubs c ON r.club_id = c.id
            WHERE r.week = ? AND c.club_name = ?
            ORDER BY r.profit DESC
        """
        df = pd.read_sql_query(query, conn, params=[week, club_name])
    else:
        query = """
            SELECT 
                r.year as año,
                r.week as semana,
                c.club_name as club,
                COALESCE(p.real_name, 'Sin asignar') as jugador,
                r.raw_nickname as nickname,
                r.profit,
                r.rake,
                r.total as balance
            FROM records r
            LEFT JOIN players p ON r.player_id = p.id
            JOIN clubs c ON r.club_id = c.id
            WHERE r.week = ?
            ORDER BY c.club_name, r.profit DESC
        """
        df = pd.read_sql_query(query, conn, params=[week])
    
    conn.close()
    return df

def get_available_weeks(club_name: str = None):
    """Obtiene lista de semanas disponibles, opcionalmente filtrada por club."""
    conn = get_connection()
    
    if club_name and club_name != "Todos":
        query = """
            SELECT DISTINCT r.week, r.year
            FROM records r
            JOIN clubs c ON r.club_id = c.id
            WHERE c.club_name = ?
            ORDER BY r.year DESC, r.week DESC
        """
        cursor = conn.cursor()
        cursor.execute(query, (club_name,))
    else:
        query = """
            SELECT DISTINCT week, year
            FROM records
            ORDER BY year DESC, week DESC
        """
        cursor = conn.cursor()
        cursor.execute(query)
    
    weeks = [(row[0], row[1]) for row in cursor.fetchall()]
    conn.close()
    return weeks

def add_weekly_record(year: int, week: str, club_id: int, player_id: int, 
                      nickname: str, profit: float, rake: float, total: float = None):
    """Agrega un registro semanal."""
    if total is None:
        total = profit - rake
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO records (year, week, club_id, player_id, raw_nickname, profit, rake, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (year, week, club_id, player_id, nickname, profit, rake, total))
        conn.commit()
        return True, "Registro agregado exitosamente"
    except Exception as e:
        return False, f"Error al agregar registro: {e}"
    finally:
        conn.close()

def add_multiple_weekly_records(records_data: list):
    """Agrega múltiples registros semanales de una vez."""
    conn = get_connection()
    cursor = conn.cursor()
    success_count = 0
    error_count = 0
    
    for record in records_data:
        try:
            total = record.get('total', record['profit'] - record['rake'])
            cursor.execute("""
                INSERT INTO records (year, week, club_id, player_id, raw_nickname, profit, rake, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['year'], record['week'], record['club_id'], 
                record['player_id'], record['nickname'], 
                record['profit'], record['rake'], total
            ))
            success_count += 1
        except Exception as e:
            error_count += 1
    
    conn.commit()
    conn.close()
    return success_count, error_count
