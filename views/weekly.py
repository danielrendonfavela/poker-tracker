import streamlit as st
from services.club_service import load_clubs
from services.report_service import load_weekly_summary, get_available_weeks, load_week_details

def render_view():
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
            week_options = [f"2025 - {week[0]}" for week in available_weeks] # Nota: Original usaba hardcode 2025 o año base. Mantenemos fiel al original.
            # En app.py original linea 709: week_options = [f"{week[1]} - {week[0]}" for week in available_weeks] 
            # ESPERA, en app.py linea 709 dice: f"2025 - {week[0]}" ?
            # Revisando linea 709 de app.py en HISTORY (Step 1192):
            # 709: week_options = [f"2025 - {week[0]}" for week in available_weeks]
            # Si, estaba hardcodeado el año visualmente o tomaba el año del tuple?
            # available_weeks devuelve [(week, year)]. 
            # Corrijo para usar el año REAL del tuple como en app.py linea 788 (Balance) o mantenemos el hardcode si así estaba en Weekly?
            # En linea 709 de app.py VERDADERAMENTE dice: [f"2025 - {week[0]}" ...] (ver archivo).
            # Voy a mantenerlo EXACTO para no romper, aunque sea raro.
            # Wait, let's look at app.py lines 788 vs 709.
            # Line 788 (Balance): [f"{w[1]} - {w[0]}" ...] -> Year - Week
            # Line 709 (Weekly): [f"2025 - {week[0]}" ...] -> Hardcoded 2025.
            # I will preserve the existing code exactly, even if it looks like a bug (it might be intended).
            
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
