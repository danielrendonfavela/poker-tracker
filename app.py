"""
Poker Tracker - Aplicación Streamlit
Dashboard para gestionar la contabilidad de jugadores en clubes de poker.
Todos los cálculos se realizan dinámicamente desde la base de datos.
"""
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import os

# Configuración de la página
st.set_page_config(
    page_title="Poker Tracker",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATABASE_PATH = "poker_tracker.db"


def get_connection():
    """Obtiene una conexión a la base de datos."""
    return sqlite3.connect(DATABASE_PATH)


# ============================================
# FUNCIONES DE CARGA DE DATOS (Dinámicas)
# ============================================

def load_players():
    """Carga todos los jugadores de la base de datos."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM players ORDER BY real_name", conn)
    conn.close()
    return df


def load_clubs():
    """Carga todos los clubes de la base de datos."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM clubs ORDER BY club_name", conn)
    conn.close()
    return df


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


def load_nickname_count():
    """Cuenta el número total de nicknames únicos en la DB."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT original_nick) FROM nickname_mappings")
    count = cursor.fetchone()[0]
    conn.close()
    return count


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


def get_club_id(club_name: str):
    """Obtiene el ID de un club por nombre."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clubs WHERE club_name = ?", (club_name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


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


# ============================================
# APLICACIÓN PRINCIPAL
# ============================================

def main():
    # Header
    st.title("🎰 Poker Tracker")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("📊 Navegación")
    page = st.sidebar.radio(
        "Selecciona una sección:",
        ["🏠 Dashboard", "👥 Jugadores", "🏢 Clubes", "📅 Por Semana", "💰 Balance", "📝 Registros", "➕ Agregar Datos"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Poker Tracker v1.0**\n\n"
        "Sistema de gestión de contabilidad para clubes de poker."
    )
    
    # ==========================================
    # PÁGINA: DASHBOARD
    # ==========================================
    if page == "🏠 Dashboard":
        st.header("Dashboard")
        
        # Cargar estadísticas dinámicamente
        stats = load_dashboard_stats()
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Jugadores", stats['players'])
        
        with col2:
            st.metric("🏢 Clubes", stats['clubs'])
        
        with col3:
            st.metric("📝 Registros", f"{stats['records']:,}")
        
        with col4:
            st.metric("📅 Semanas", stats['weeks'])
        
        # Segunda fila de métricas
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎮 Nicknames", stats['nicknames'])
        
        with col2:
            st.metric("💰 Profit Total", f"${stats['total_profit']:,.2f}")
        
        with col3:
            st.metric("🎲 Rake Total", f"${stats['total_rake']:,.2f}")
        
        with col4:
            st.metric("📊 Balance Total", f"${stats['total_balance']:,.2f}")
        
        # Resumen por club
        st.markdown("---")
        st.subheader("📊 Resumen por Club")
        
        club_summary = load_club_summary()
        if not club_summary.empty:
            st.dataframe(
                club_summary,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "club": "Club",
                    "registros": st.column_config.NumberColumn("Registros", format="%d"),
                    "jugadores": st.column_config.NumberColumn("Jugadores", format="%d"),
                    "semanas": st.column_config.NumberColumn("Semanas", format="%d"),
                    "profit_total": st.column_config.NumberColumn("Profit Total", format="$%.2f"),
                    "rake_total": st.column_config.NumberColumn("Rake Total", format="$%.2f"),
                    "balance_total": st.column_config.NumberColumn("Balance Total", format="$%.2f"),
                }
            )
    
    # ==========================================
    # PÁGINA: JUGADORES
    # ==========================================
    elif page == "👥 Jugadores":
        st.header("👥 Gestión de Jugadores")
        
        tab1, tab2 = st.tabs(["📊 Resumen de Ganancias", "🎮 Nicknames por Jugador"])
        
        with tab1:
            st.subheader("Resumen de Ganancias por Jugador")
            
            player_summary = load_player_summary()
            
            if not player_summary.empty:
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    search = st.text_input("🔍 Buscar jugador", placeholder="Ej: Sergio")
                with col2:
                    sort_by = st.selectbox("Ordenar por", ["profit_total", "rake_total", "partidas"])
                
                # Aplicar filtros
                filtered = player_summary.copy()
                if search:
                    filtered = filtered[filtered['jugador'].str.contains(search, case=False, na=False)]
                
                filtered = filtered.sort_values(sort_by, ascending=False)
                
                # Métricas rápidas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Jugadores", len(filtered))
                with col2:
                    st.metric("Profit Total", f"${filtered['profit_total'].sum():,.2f}")
                with col3:
                    st.metric("Rake Total", f"${filtered['rake_total'].sum():,.2f}")
                with col4:
                    st.metric("Partidas", f"{filtered['partidas'].sum():,}")
                
                st.markdown("---")
                
                # Tabla
                st.dataframe(
                    filtered,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "jugador": "Jugador",
                        "partidas": st.column_config.NumberColumn("Partidas", format="%d"),
                        "profit_total": st.column_config.NumberColumn("Profit Total", format="$%.2f"),
                        "rake_total": st.column_config.NumberColumn("Rake Total", format="$%.2f"),
                        "balance_total": st.column_config.NumberColumn("Balance", format="$%.2f"),
                        "clubes": st.column_config.NumberColumn("Clubes", format="%d"),
                    }
                )
            else:
                st.info("No hay datos de jugadores aún.")
        
        with tab2:
            st.subheader("Nicknames por Jugador")
            
            player_nicks = load_player_nicknames()
            
            if not player_nicks.empty:
                # Filtro
                search_nick = st.text_input("🔍 Buscar por nombre o nickname", placeholder="Ej: arenito")
                
                filtered_nicks = player_nicks.copy()
                if search_nick:
                    mask = (
                        filtered_nicks['nombre_real'].str.contains(search_nick, case=False, na=False) |
                        filtered_nicks['nicknames'].str.contains(search_nick, case=False, na=False)
                    )
                    filtered_nicks = filtered_nicks[mask]
                
                st.dataframe(
                    filtered_nicks,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "nombre_real": "Nombre Real",
                        "nicknames": st.column_config.TextColumn("Nicknames", width="large"),
                        "num_nicknames": st.column_config.NumberColumn("# Nicks", format="%d"),
                        "clubes": st.column_config.TextColumn("Clubes", width="medium"),
                        "num_clubes": st.column_config.NumberColumn("# Clubes", format="%d"),
                    }
                )
            else:
                st.info("No hay datos de nicknames aún.")
    
    # ==========================================
    # PÁGINA: CLUBES
    # ==========================================
    elif page == "🏢 Clubes":
        st.header("🏢 Gestión de Clubes")
        
        club_summary = load_club_summary()
        
        if not club_summary.empty:
            # Métricas generales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Clubes", len(club_summary))
            with col2:
                st.metric("Profit Total", f"${club_summary['profit_total'].sum():,.2f}")
            with col3:
                st.metric("Rake Total", f"${club_summary['rake_total'].sum():,.2f}")
            with col4:
                st.metric("Registros Totales", f"{club_summary['registros'].sum():,}")
            
            st.markdown("---")
            
            # Tabla de clubes
            st.subheader("Detalle por Club")
            st.dataframe(
                club_summary,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "club": "Club",
                    "registros": st.column_config.NumberColumn("Registros", format="%d"),
                    "jugadores": st.column_config.NumberColumn("Jugadores", format="%d"),
                    "semanas": st.column_config.NumberColumn("Semanas", format="%d"),
                    "profit_total": st.column_config.NumberColumn("Profit Total", format="$%.2f"),
                    "rake_total": st.column_config.NumberColumn("Rake Total", format="$%.2f"),
                    "balance_total": st.column_config.NumberColumn("Balance", format="$%.2f"),
                }
            )
        else:
            st.warning("No hay clubes registrados.")
    
    # ==========================================
    # PÁGINA: POR SEMANA
    # ==========================================
    elif page == "📅 Por Semana":
        st.header("📅 Resultados por Semana")
        
        # Filtro por club (primero)
        clubs = load_clubs()
        club_options = ["Todos"] + sorted(clubs['club_name'].tolist())
        selected_club = st.selectbox("🏢 Seleccionar Club", club_options, 
                                      help="Selecciona un club para ver sus resultados semanales")
        
        st.markdown("---")
        
        # Tabs para resumen y detalle
        tab1, tab2 = st.tabs(["📊 Resumen Semanal", "🔍 Detalle por Semana"])
        
        with tab1:
            weekly_summary = load_weekly_summary(selected_club)
            
            if not weekly_summary.empty:
                # Métricas calculadas dinámicamente
                col1, col2, col3, col4 = st.columns(4)
                
                unique_weeks = weekly_summary['semana'].nunique()
                with col1:
                    st.metric("Total Semanas", unique_weeks)
                with col2:
                    st.metric("Profit Total", f"${weekly_summary['profit_total'].sum():,.2f}")
                with col3:
                    st.metric("Rake Total", f"${weekly_summary['rake_total'].sum():,.2f}")
                with col4:
                    avg_jugadores = weekly_summary['jugadores'].sum() / unique_weeks if unique_weeks > 0 else 0
                    st.metric("Jugadores Promedio/Semana", f"{avg_jugadores:.1f}")
                
                st.markdown("---")
                
                # Información de contexto
                if selected_club != "Todos":
                    st.info(f"📊 Mostrando resultados semanales para **{selected_club}**")
                else:
                    st.info("📊 Mostrando resultados de **todos los clubes**. Selecciona un club específico para ver sus datos individualmente.")
                
                # Tabla
                st.dataframe(
                    weekly_summary,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "semana": "Semana",
                        "club": "Club",
                        "registros": st.column_config.NumberColumn("Registros", format="%d"),
                        "jugadores": st.column_config.NumberColumn("Jugadores", format="%d"),
                        "profit_total": st.column_config.NumberColumn("Profit Total", format="$%.2f"),
                        "rake_total": st.column_config.NumberColumn("Rake Total", format="$%.2f"),
                        "balance_total": st.column_config.NumberColumn("Balance", format="$%.2f"),
                    }
                )
                
                st.caption(f"Mostrando {len(weekly_summary)} registros semanales")
            else:
                st.info("No hay registros semanales aún.")
        
        with tab2:
            st.subheader("🔍 Detalle de Semana Específica")
            
            # Obtener semanas disponibles
            available_weeks = get_available_weeks(selected_club)
            
            if available_weeks:
                # Crear opciones con año
                week_options = [f"2025 - {week[0]}" for week in available_weeks]
                selected_week_display = st.selectbox(
                    "Selecciona una semana",
                    week_options,
                    help="Selecciona una semana para ver los detalles de cada jugador"
                )
                
                # Extraer solo el nombre de la semana (sin el año)
                selected_week = selected_week_display.split(" - ", 1)[1] if " - " in selected_week_display else selected_week_display
                
                st.markdown("---")
                
                # Cargar detalles de la semana
                week_details = load_week_details(selected_week, selected_club)
                
                if not week_details.empty:
                    # Métricas de la semana
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Jugadores", len(week_details))
                    with col2:
                        st.metric("Profit Total", f"${week_details['profit'].sum():,.2f}")
                    with col3:
                        st.metric("Rake Total", f"${week_details['rake'].sum():,.2f}")
                    with col4:
                        st.metric("Balance Total", f"${week_details['balance'].sum():,.2f}")
                    
                    st.markdown("---")
                    
                    # Información de contexto
                    st.success(f"📆 **Semana: {selected_week_display}**" + 
                              (f" | Club: **{selected_club}**" if selected_club != "Todos" else ""))
                    
                    # Tabla de jugadores
                    st.dataframe(
                        week_details,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "año": st.column_config.NumberColumn("Año", format="%d"),
                            "semana": "Semana",
                            "club": "Club",
                            "jugador": "Jugador",
                            "nickname": "Nickname",
                            "profit": st.column_config.NumberColumn("Profit", format="$%.2f"),
                            "rake": st.column_config.NumberColumn("Rake", format="$%.2f"),
                            "balance": st.column_config.NumberColumn("Balance", format="$%.2f"),
                        }
                    )
                    
                    # Top ganadores y perdedores
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🏆 Top 5 Ganadores")
                        top_winners = week_details.nlargest(5, 'profit')[['jugador', 'nickname', 'profit']]
                        st.dataframe(top_winners, hide_index=True, use_container_width=True)
                    
                    with col2:
                        st.subheader("📉 Top 5 Perdedores")
                        top_losers = week_details.nsmallest(5, 'profit')[['jugador', 'nickname', 'profit']]
                        st.dataframe(top_losers, hide_index=True, use_container_width=True)
                else:
                    st.warning("No hay datos para esta semana.")
            else:
                st.info("No hay semanas disponibles para el club seleccionado.")
    
    # ==========================================
    # PÁGINA: BALANCE
    # ==========================================
    elif page == "💰 Balance":
        st.header("💰 Balance del Club")
        
        # Selector de semana
        available_weeks = get_available_weeks()
        
        if available_weeks:
            # Selector de semana arriba
            week_options = [f"{w[1]} - {w[0]}" for w in available_weeks]
            selected_week_display = st.selectbox("📅 Seleccionar Semana", week_options)
            selected_week = selected_week_display.split(" - ", 1)[1] if " - " in selected_week_display else selected_week_display
            
            st.markdown("---")
            
            # Configuración por club con valores por defecto del Excel
            # Formato: {club_name: {'comision': %, 'rb': %, 'tc': tipo_cambio}}
            default_config = {
                'PATOS MX': {'comision': 11.0, 'rb': 42.4, 'tc': 10.0},
                'PP PATOS MX': {'comision': 20.0, 'rb': 46.0, 'tc': 10.0},
                'X': {'comision': 35.0, 'rb': 32.0, 'tc': 5.0},
                'Suprema': {'comision': 20.0, 'rb': 30.0, 'tc': 10.0},
                'Club GG RAGNAR': {'comision': 40.0, 'rb': 30.0, 'tc': 1.0},
                'Paradise': {'comision': 20.0, 'rb': 30.0, 'tc': 10.0},
                'PPP': {'comision': 50.0, 'rb': 30.0, 'tc': 10.0},
                'Mata Ases': {'comision': 20.0, 'rb': 54.0, 'tc': 10.0},
                'Bros': {'comision': 20.0, 'rb': 30.0, 'tc': 10.0},
                'Club GG NPM': {'comision': 40.0, 'rb': 30.0, 'tc': 1.0},
                'Barret': {'comision': 20.0, 'rb': 30.0, 'tc': 10.0},
            }
            
            # Inicializar session state para configuración de clubs
            if 'club_config' not in st.session_state:
                st.session_state.club_config = default_config.copy()
            
            # Obtener clubs de la semana seleccionada
            conn = get_connection()
            query = """
                SELECT 
                    c.club_name as club,
                    COALESCE(SUM(r.rake), 0) as rake_total
                FROM records r
                JOIN clubs c ON r.club_id = c.id
                WHERE r.week = ?
                GROUP BY c.club_name
                ORDER BY rake_total DESC
            """
            balance_df = pd.read_sql_query(query, conn, params=[selected_week])
            conn.close()
            
            if not balance_df.empty:
                # Configuración por club en expander
                with st.expander("⚙️ Configuración por Club (click para editar)", expanded=False):
                    st.caption("Ajusta las tasas de comisión, rakeback y tipo de cambio para cada club")
                    
                    # Crear columnas para los clubs presentes en la semana
                    clubs_in_week = balance_df['club'].tolist()
                    
                    # Mostrar configuración en grid
                    for i in range(0, len(clubs_in_week), 2):
                        cols = st.columns(2)
                        for j, col in enumerate(cols):
                            if i + j < len(clubs_in_week):
                                club = clubs_in_week[i + j]
                                with col:
                                    st.markdown(f"**{club}**")
                                    config = st.session_state.club_config.get(club, {'comision': 20.0, 'rb': 30.0, 'tc': 10.0})
                                    
                                    c1, c2, c3 = st.columns(3)
                                    with c1:
                                        new_com = st.number_input(f"Com%", value=config['comision'], 
                                                                   min_value=0.0, max_value=100.0, step=1.0,
                                                                   key=f"com_{club}")
                                    with c2:
                                        new_rb = st.number_input(f"RB%", value=config['rb'],
                                                                  min_value=0.0, max_value=100.0, step=1.0,
                                                                  key=f"rb_{club}")
                                    with c3:
                                        new_tc = st.number_input(f"TC", value=config['tc'],
                                                                  min_value=0.1, max_value=50.0, step=0.5,
                                                                  key=f"tc_{club}")
                                    
                                    # Actualizar configuración
                                    st.session_state.club_config[club] = {
                                        'comision': new_com, 'rb': new_rb, 'tc': new_tc
                                    }
                
                st.markdown("---")
                
                # Calcular valores por club usando configuración individual
                def calc_for_club(row):
                    club = row['club']
                    config = st.session_state.club_config.get(club, {'comision': 20.0, 'rb': 30.0, 'tc': 10.0})
                    rake = row['rake_total']
                    comision = rake * (config['comision'] / 100)
                    rb = rake * (config['rb'] / 100)
                    total = rake - comision - rb
                    mxn = total * config['tc']
                    return pd.Series({
                        'comision': comision,
                        'rakeback': rb,
                        'total_usd': total,
                        'mxn': mxn,
                        'tc_used': config['tc'],
                        'com_pct': config['comision'],
                        'rb_pct': config['rb']
                    })
                
                # Aplicar cálculos
                calcs = balance_df.apply(calc_for_club, axis=1)
                balance_df = pd.concat([balance_df, calcs], axis=1)
                
                # Profit total
                profit_mxn_total = balance_df['mxn'].sum()
                
                # Layout: Tabla + Profit
                col1, col2 = st.columns([2.5, 1])
                
                with col1:
                    st.markdown(f"### 📊 Semana: {selected_week_display}")
                    
                    # Tabla de balance con configuración individual
                    display_df = balance_df[['club', 'rake_total', 'com_pct', 'comision', 'rb_pct', 'rakeback', 'total_usd', 'tc_used', 'mxn']].copy()
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "club": "App / Club",
                            "rake_total": st.column_config.NumberColumn("Rake", format="$%.2f"),
                            "com_pct": st.column_config.NumberColumn("Com%", format="%.0f%%"),
                            "comision": st.column_config.NumberColumn("Comisión", format="$%.2f"),
                            "rb_pct": st.column_config.NumberColumn("RB%", format="%.0f%%"),
                            "rakeback": st.column_config.NumberColumn("RB", format="$%.2f"),
                            "total_usd": st.column_config.NumberColumn("Total", format="$%.2f"),
                            "tc_used": st.column_config.NumberColumn("TC", format="×%.1f"),
                            "mxn": st.column_config.NumberColumn("MXN", format="$%.2f"),
                        }
                    )
                
                with col2:
                    st.markdown("### 💵 Profit Club")
                    st.markdown(
                        f"""
                        <div style="background-color: #2E7D32; padding: 20px; border-radius: 10px; text-align: center;">
                            <h2 style="color: white; margin: 0;">${profit_mxn_total:,.2f}</h2>
                            <p style="color: #C8E6C9; margin: 5px 0;">MXN Total</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    st.markdown("---")
                    
                    # Métricas
                    st.metric("Rake Total", f"${balance_df['rake_total'].sum():,.2f}")
                    st.metric("Comisión Total", f"${balance_df['comision'].sum():,.2f}")
                    st.metric("Rakeback Total", f"${balance_df['rakeback'].sum():,.2f}")
                
                st.markdown("---")
                
                # Gráfico de barras
                st.markdown("### 📈 Comparativo por Club (MXN)")
                
                import plotly.express as px
                
                fig = px.bar(
                    balance_df,
                    x='club',
                    y='mxn',
                    title=f"Profit por Club - {selected_week_display}",
                    labels={'club': 'Club', 'mxn': 'MXN'},
                    color='mxn',
                    color_continuous_scale='Greens'
                )
                fig.update_layout(
                    xaxis_tickangle=-45,
                    showlegend=False,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning(f"No hay datos para la semana {selected_week_display}")
        else:
            st.info("No hay semanas disponibles. Agrega registros primero.")
    
    # ==========================================
    # PÁGINA: REGISTROS
    # ==========================================
    elif page == "📝 Registros":
        st.header("📝 Registros de Partidas")
        
        records = load_records()
        
        if not records.empty:
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                weeks = ["Todas"] + sorted(records['week'].unique().tolist(), reverse=True)
                selected_week = st.selectbox("Semana", weeks)
            
            with col2:
                clubs_list = ["Todos"] + sorted(records['club'].dropna().unique().tolist())
                selected_club = st.selectbox("Club", clubs_list)
            
            with col3:
                players_list = ["Todos"] + sorted(records['player'].dropna().unique().tolist())
                selected_player = st.selectbox("Jugador", players_list)
            
            # Aplicar filtros
            filtered = records.copy()
            if selected_week != "Todas":
                filtered = filtered[filtered['week'] == selected_week]
            if selected_club != "Todos":
                filtered = filtered[filtered['club'] == selected_club]
            if selected_player != "Todos":
                filtered = filtered[filtered['player'] == selected_player]
            
            # Métricas calculadas dinámicamente
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Registros", f"{len(filtered):,}")
            with col2:
                st.metric("Profit Total", f"${filtered['profit'].sum():,.2f}")
            with col3:
                st.metric("Rake Total", f"${filtered['rake'].sum():,.2f}")
            with col4:
                st.metric("Balance Total", f"${filtered['total'].sum():,.2f}")
            
            st.markdown("---")
            
            # Tabla
            st.dataframe(
                filtered,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "week": "Semana",
                    "player": "Jugador",
                    "club": "Club",
                    "raw_nickname": "Nickname",
                    "profit": st.column_config.NumberColumn("Profit", format="$%.2f"),
                    "rake": st.column_config.NumberColumn("Rake", format="$%.2f"),
                    "total": st.column_config.NumberColumn("Total", format="$%.2f"),
                }
            )
            
            st.info(f"Mostrando {len(filtered):,} de {len(records):,} registros")
        else:
            st.info("No hay registros de partidas aún.")
    
    # ==========================================
    # PÁGINA: AGREGAR DATOS
    # ==========================================
    elif page == "➕ Agregar Datos":
        st.header("➕ Agregar Nuevos Datos")
        
        tab1, tab2, tab3 = st.tabs(["👤 Nuevo Jugador", "📅 Nueva Semana", "📤 Re-importar Datos"])
        
        # ===== TAB 1: NUEVO JUGADOR =====
        with tab1:
            st.subheader("Agregar Nuevo Jugador")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ➕ Registro de Jugador")
                
                with st.form("add_player_form", clear_on_submit=True):
                    real_name = st.text_input("Nombre Real *", placeholder="Ej: Juan Pérez")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        status = st.selectbox("Estado", ["active", "inactive", "banned"])
                    with col_b:
                        nickname = st.text_input("Nickname (opcional)", placeholder="Ej: ElPro123")
                    
                    club_for_nick = st.selectbox(
                        "Club para el nickname (opcional)",
                        ["Ninguno"] + sorted(load_clubs()['club_name'].tolist())
                    )
                    
                    submitted = st.form_submit_button("➕ Agregar Jugador", use_container_width=True)
                    
                    if submitted:
                        if real_name.strip():
                            success, message, player_id = add_player(real_name.strip(), status)
                            
                            if success:
                                st.success(message)
                                
                                # Si hay nickname y club, agregar el mapeo
                                if nickname.strip() and club_for_nick != "Ninguno" and player_id:
                                    club_id = get_club_id(club_for_nick)
                                    if club_id:
                                        nick_success, nick_msg = add_nickname_mapping(
                                            nickname.strip(), player_id, club_id
                                        )
                                        if nick_success:
                                            st.success(f"Nickname '{nickname}' mapeado a {club_for_nick}")
                                        else:
                                            st.warning(nick_msg)
                            else:
                                st.warning(message)
                        else:
                            st.error("Por favor ingresa un nombre.")
            
            with col2:
                st.markdown("### 📋 Jugadores Registrados")
                players = load_players()
                if not players.empty:
                    st.dataframe(
                        players[['real_name', 'status']].head(15),
                        hide_index=True,
                        use_container_width=True
                    )
                    st.caption(f"Mostrando 15 de {len(players)} jugadores")
                else:
                    st.info("No hay jugadores registrados.")
        
        # ===== TAB 2: NUEVA SEMANA =====
        with tab2:
            st.subheader("📅 Registrar Nueva Semana")
            
            # Configuración de la semana
            st.markdown("### Configuración de la Semana")
            
            col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 2])
            
            with col1:
                from datetime import datetime, timedelta
                # Selector de fecha de inicio
                start_date = st.date_input(
                    "📅 Fecha Inicio",
                    value=datetime.now().date() - timedelta(days=datetime.now().weekday()),
                    help="Selecciona el lunes de la semana"
                )
            
            with col2:
                # Calcular fecha fin automáticamente (6 días después)
                end_date = st.date_input(
                    "📅 Fecha Fin", 
                    value=start_date + timedelta(days=6),
                    help="Automáticamente 6 días después del inicio"
                )
            
            with col3:
                clubs = load_clubs()
                selected_club = st.selectbox("🏢 Club", clubs['club_name'].tolist())
            
            with col4:
                # Generar el formato de semana automáticamente
                meses_es = {
                    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                    7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                }
                week_format = f"{start_date.day} {meses_es[start_date.month]} / {end_date.day} {meses_es[end_date.month]}"
                year = start_date.year
                
                st.markdown("##### Semana generada:")
                st.success(f"**{year} - {week_format}**")
            
            st.markdown("---")
            
            # Subtabs para registro individual vs masivo
            subtab1, subtab2 = st.tabs(["📝 Registro Individual", "📊 Registro Múltiple"])
            
            with subtab1:
                st.markdown("### Agregar Registro Individual")
                
                players_dict = get_all_players_dict()
                player_names = ["Seleccionar..."] + list(players_dict.keys())
                
                with st.form("add_single_record", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        selected_player = st.selectbox("Jugador", player_names)
                        nickname_record = st.text_input("Nickname usado", placeholder="Ej: ProPlayer")
                    
                    with col2:
                        profit = st.number_input("Profit", value=0.0, step=10.0, format="%.2f")
                        rake = st.number_input("Rake", value=0.0, step=10.0, format="%.2f")
                    
                    # Calcular balance automáticamente
                    balance = profit - rake
                    st.info(f"💰 Balance calculado: **${balance:,.2f}**")
                    
                    submit_record = st.form_submit_button("➕ Agregar Registro", use_container_width=True)
                    
                    if submit_record:
                        if selected_player == "Seleccionar...":
                            st.error("Por favor selecciona un jugador.")
                        elif not nickname_record.strip():
                            st.error("Por favor ingresa el nickname usado.")
                        else:
                            player_id = players_dict.get(selected_player)
                            club_id = get_club_id(selected_club)
                            
                            if player_id and club_id:
                                success, msg = add_weekly_record(
                                    year, week_format.strip(), club_id, player_id,
                                    nickname_record.strip(), profit, rake, balance
                                )
                                if success:
                                    st.success(f"✅ Registro agregado: {selected_player} en {week_format}")
                                else:
                                    st.error(msg)
                            else:
                                st.error("Error al obtener IDs. Verifica jugador y club.")
            
            with subtab2:
                st.markdown("### Registro Múltiple de Jugadores")
                
                st.success(f"📅 Configuración: **{year} - {week_format}** | Club: **{selected_club}**")
                
                # Usar session state para mantener los registros
                if 'pending_records' not in st.session_state:
                    st.session_state.pending_records = []
                
                # Formulario para agregar a la lista
                st.markdown("#### Agregar jugador a la lista")
                
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1.5, 1])
                
                with col1:
                    players_dict = get_all_players_dict()
                    batch_player = st.selectbox("Jugador", ["Seleccionar..."] + list(players_dict.keys()), key="batch_player")
                with col2:
                    batch_nick = st.text_input("Nickname", key="batch_nick", placeholder="Nickname")
                with col3:
                    batch_profit = st.number_input("Profit", value=0.0, step=10.0, key="batch_profit")
                with col4:
                    batch_rake = st.number_input("Rake", value=0.0, step=10.0, key="batch_rake")
                with col5:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    if st.button("➕ Agregar", use_container_width=True):
                        if batch_player != "Seleccionar..." and batch_nick.strip():
                            player_id = players_dict.get(batch_player)
                            club_id = get_club_id(selected_club)
                            st.session_state.pending_records.append({
                                'year': year,
                                'week': week_format,
                                'club_id': club_id,
                                'player_id': player_id,
                                'player_name': batch_player,
                                'nickname': batch_nick.strip(),
                                'profit': batch_profit,
                                'rake': batch_rake,
                                'balance': batch_profit - batch_rake
                            })
                            st.rerun()
                
                # Mostrar registros pendientes
                if st.session_state.pending_records:
                    st.markdown("#### 📋 Registros pendientes de guardar")
                    
                    pending_df = pd.DataFrame(st.session_state.pending_records)
                    display_df = pending_df[['player_name', 'nickname', 'profit', 'rake', 'balance']]
                    display_df.columns = ['Jugador', 'Nickname', 'Profit', 'Rake', 'Balance']
                    
                    st.dataframe(display_df, hide_index=True, use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Registros", len(pending_df))
                    with col2:
                        st.metric("Profit Total", f"${pending_df['profit'].sum():,.2f}")
                    with col3:
                        st.metric("Rake Total", f"${pending_df['rake'].sum():,.2f}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Guardar Todos los Registros", type="primary", use_container_width=True):
                            success_count, error_count = add_multiple_weekly_records(st.session_state.pending_records)
                            st.success(f"✅ {success_count} registros guardados exitosamente!")
                            if error_count > 0:
                                st.warning(f"⚠️ {error_count} registros con errores")
                            st.session_state.pending_records = []
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️ Limpiar Lista", use_container_width=True):
                            st.session_state.pending_records = []
                            st.rerun()
                else:
                    st.info("Agrega jugadores a la lista usando el formulario de arriba.")
        
        # ===== TAB 3: RE-IMPORTAR =====
        with tab3:
            st.subheader("📤 Re-importar Datos desde Excel")
            st.warning(
                "⚠️ **Precaución**\n\n"
                "Esta acción re-importará todos los datos del archivo Excel original. "
                "Se recomienda hacer un respaldo de la base de datos antes de continuar."
            )
            
            if st.button("🔄 Re-importar desde Excel"):
                st.info("Funcionalidad próximamente disponible...")


if __name__ == "__main__":
    main()
