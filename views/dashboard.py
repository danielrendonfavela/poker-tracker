import streamlit as st
from services.report_service import load_dashboard_stats
from services.club_service import load_club_summary

def render_view():
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
