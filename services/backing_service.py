from datetime import datetime
import sqlite3
from services.database import get_connection

def get_active_deal(player_id: int):
    """Retorna el deal activo para un jugador, si existe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, player_id, deal_percentage, makeup_balance, created_at
        FROM backing_deals
        WHERE player_id = ? AND is_active = 1
    """, (player_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'player_id': row[1],
            'deal_percentage': row[2],
            'makeup_balance': row[3],
            'created_at': row[4]
        }
    return None

def create_or_update_deal(player_id: int, percentage: float, initial_makeup: float = 0.0):
    """Crea un nuevo deal o actualiza si ya existe."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE backing_deals SET is_active = 0 WHERE player_id = ?", (player_id,))
    
    cursor.execute("""
        INSERT INTO backing_deals (player_id, deal_percentage, makeup_balance)
        VALUES (?, ?, ?)
    """, (player_id, percentage, initial_makeup))
    
    conn.commit()
    conn.close()
    return True

def get_all_deals_status():
    """Obtiene el estado de todos los jugadores con deals activos."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.real_name,
            p.id,
            d.deal_percentage,
            d.makeup_balance
        FROM backing_deals d
        JOIN players p ON d.player_id = p.id
        WHERE d.is_active = 1
        ORDER BY p.real_name
    """)
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'player': row[0],
            'player_id': row[1],
            'deal_percentage': row[2],
            'current_makeup': row[3]
        })
    conn.close()
    return results

# --- LÓGICA DE LIQUIDACIÓN GLOBAL ---

def preview_settlement(player_id: int, week: str, bonuses: float, fees: float):
    """
    Calcula una vista previa del corte semanal global (sin guardar).
    Suma profits de todos los clubes + Bonos - Fees.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Calcular Gross Profit (Suma de profits de records)
    cursor.execute("""
        SELECT COALESCE(SUM(profit), 0)
        FROM records
        WHERE player_id = ? AND week = ?
    """, (player_id, week))
    total_gross = cursor.fetchone()[0]
    
    # 2. Obtener Deal
    deal = get_active_deal_internal(cursor, player_id)
    if not deal:
        conn.close()
        return None # No se puede calcular sin deal activo
    
    deal_pct = deal['deal_percentage']
    current_makeup = deal['makeup_balance']
    conn.close()
    
    # 3. Calcular Resultado Neto
    net_result = total_gross + bonuses - fees
    
    # 4. Aplicar Lógica Backing
    settlement = calculate_distribution(net_result, deal_pct, current_makeup)
    
    # Agregar metadatos
    settlement['total_gross_profit'] = total_gross
    settlement['bonuses'] = bonuses
    settlement['fees'] = fees
    
    return settlement

def save_settlement(player_id: int, week: str, bonuses: float, fees: float):
    """
    Guarda el corte semanal en `weekly_settlements` y actualiza la deuda en `backing_deals`.
    """
    preview = preview_settlement(player_id, week, bonuses, fees)
    if not preview:
        return False
        
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Guardar Settlement
        cursor.execute("""
            INSERT INTO weekly_settlements 
            (week, player_id, total_gross_profit, bonuses, fees, net_result, player_share, club_share, makeup_change)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            week, player_id, 
            preview['total_gross_profit'], preview['bonuses'], preview['fees'], 
            preview['net_result'], preview['player_share'], preview['club_share'], 
            preview['makeup_change']
        ))
        
        # 2. Actualizar Deuda en Deal Activo
        cursor.execute("""
            UPDATE backing_deals 
            SET makeup_balance = ? 
            WHERE player_id = ? AND is_active = 1
        """, (preview['new_makeup'], player_id))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Ya existe un corte para {week} - Player {player_id}")
        return False
    finally:
        conn.close()

def calculate_distribution(net_result: float, deal_pct: float, current_makeup: float):
    """Lógica core de distribución (pura matemática)."""
    if net_result < 0:
        # Pérdida -> Todo a Makeup
        loss = abs(net_result)
        return {
            'net_result': net_result,
            'player_share': 0.0,
            'club_share': 0.0, # Club absorbe la pérdida (en deuda)
            'makeup_change': loss,
            'new_makeup': current_makeup + loss
        }
    else:
        # Ganancia -> Pagar deuda -> Repartir
        paid_makeup = 0.0
        distributable = net_result
        
        if current_makeup > 0:
            if net_result >= current_makeup:
                paid_makeup = current_makeup
                distributable = net_result - current_makeup
            else:
                paid_makeup = net_result
                distributable = 0.0
        
        player_share = distributable * deal_pct
        club_share = distributable * (1 - deal_pct)
        # El "Club Share" financiero incluye lo recuperado
        total_club_in_pocket = paid_makeup + club_share
        
        return {
            'net_result': net_result,
            'player_share': player_share,
            'club_share': total_club_in_pocket,
            'makeup_change': -paid_makeup,
            'new_makeup': current_makeup - paid_makeup
        }

def get_active_deal_internal(cursor, player_id):
    cursor.execute("""
        SELECT id, deal_percentage, makeup_balance
        FROM backing_deals
        WHERE player_id = ? AND is_active = 1
    """, (player_id,))
    row = cursor.fetchone()
    if row:
        return {'id': row[0], 'deal_percentage': row[1], 'makeup_balance': row[2]}
    return None

def get_players_with_activity(week: str):
    """Retorna jugadores que tuvieron actividad (registros) esa semana."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT p.id, p.real_name
        FROM records r
        JOIN players p ON r.player_id = p.id
        WHERE r.week = ?
        ORDER BY p.real_name
    """, (week,))
    players = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    conn.close()
    return players
