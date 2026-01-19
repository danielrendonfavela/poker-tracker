import streamlit as st
from services.player_service import load_player_summary, load_player_nicknames

def render_view():
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
