import streamlit as st
from services.report_service import load_records

def render_view():
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
