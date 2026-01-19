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

def create_or_update_deal(player_id: int, percentage: float):
    """Crea un nuevo deal o actualiza si ya existe (desactivando el anterior)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Desactivar deals anteriores
    cursor.execute("UPDATE backing_deals SET is_active = 0 WHERE player_id = ?", (player_id,))
    
    # Crear nuevo deal
    cursor.execute("""
        INSERT INTO backing_deals (player_id, deal_percentage, makeup_balance)
        VALUES (?, ?, 0)
    """, (player_id, percentage))
    
    conn.commit()
    conn.close()
    return True

def calculate_weekly_share(profit: float, deal_pct: float, current_makeup: float):
    """
    Calcula la distribución de ganancias y cambios en el makeup.
    
    Retorna:
    - player_share: Cuánto le toca al jugador
    - club_share: Cuánto le toca al club (backer)
    - makeup_change: Cuánto aumenta (positivo) o disminuye (negativo) la deuda
    - new_makeup: Nuevo balance de la deuda
    """
    
    if profit < 0:
        # PÉRDIDA: Se suma 100% al makeup
        loss = abs(profit)
        return {
            'player_share': 0.0,
            'club_share': 0.0,
            'makeup_change': loss,
            'new_makeup': current_makeup + loss
        }
    
    else:
        # GANANCIA
        # 1. Pagar makeup primero
        remaining_profit = profit
        paid_makeup = 0.0
        
        if current_makeup > 0:
            if profit >= current_makeup:
                # Cubre toda la deuda
                paid_makeup = current_makeup
                remaining_profit = profit - current_makeup
            else:
                # Cubre parcial
                paid_makeup = profit
                remaining_profit = 0.0
        
        # 2. Dividir el resto según el deal
        player_share = remaining_profit * deal_pct
        club_share = remaining_profit * (1 - deal_pct)
        
        # El share del club incluye lo recuperado de makeup + su parte del profit
        total_club_recovery = paid_makeup + club_share
        
        return {
            'player_share': player_share,
            'club_share': total_club_recovery, # Backer se lleva lo pagado de deuda + su %
            'makeup_change': -paid_makeup,
            'new_makeup': current_makeup - paid_makeup
        }

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
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            'player': row[0],
            'player_id': row[1],
            'deal_percentage': row[2],
            'current_makeup': row[3]
        })
    return results
