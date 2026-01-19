import streamlit as st
import pandas as pd
from services import player_service, backing_service, report_service

def render_view():
    st.title("🤝 Sistema de Backing (Liquidación Global)")
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Configuración", "📊 Estado de Cuenta", "📅 Corte Semanal"])
    
    with tab1:
        render_config_tab()
    with tab2:
        render_status_tab()
    with tab3:
        render_settlement_tab()

def render_config_tab():
    st.header("Configurar Deal")
    players = player_service.get_all_players_dict()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_player = st.selectbox("Seleccionar Jugador", ["Seleccionar..."] + list(players.keys()))
    with col2:
        deal_pct = st.number_input("Porcentaje Jugador (%)", min_value=0, max_value=100, value=50, step=5)
    with col3:
        initial_makeup = st.number_input("Deuda Inicial (Makeup)", value=0.0, step=100.0)
    
    if selected_player != "Seleccionar...":
        player_id = players[selected_player]
        current_deal = backing_service.get_active_deal(player_id)
        if current_deal:
            st.info(f"ℹ️ Deal Actual: **{current_deal['deal_percentage']*100:.0f}%** | Makeup: **${current_deal['makeup_balance']:,.2f}**")
        
        if st.button("Guardar / Actualizar Deal"):
            if backing_service.create_or_update_deal(player_id, deal_pct/100.0, initial_makeup):
                st.success(f"Deal guardado para {selected_player}")
                st.rerun()

def render_status_tab():
    st.header("Estado de Jugadores con Backing")
    deals = backing_service.get_all_deals_status()
    if not deals:
        st.info("No hay deals activos.")
        return
        
    df = pd.DataFrame(deals)
    df['deal_percentage'] = (df['deal_percentage'] * 100).astype(int).astype(str) + '%'
    df.rename(columns={'player': 'Jugador', 'deal_percentage': 'Deal %', 'current_makeup': 'Makeup (Deuda)'}, inplace=True)
    
    st.dataframe(
        df[['Jugador', 'Deal %', 'Makeup (Deuda)']].style.format({"Makeup (Deuda)": "${:,.2f}"})
        .applymap(lambda v: 'color: red; font-weight: bold' if v > 0 else '', subset=['Makeup (Deuda)']),
        use_container_width=True
    )

def render_settlement_tab():
    st.header("Corte Semanal Global")
    st.caption("Selecciona una semana y un jugador para realizar el corte final (todos los clubes incluidos).")
    
    # 1. Seleccionar Semana
    weeks_data = report_service.get_available_weeks()
    # weeks_data es lista de tuplas (week, year). Extraemos solo week.
    weeks = [w[0] for w in weeks_data]
    selected_week = st.selectbox("Semana de Corte", weeks)
    
    if not selected_week:
        return

    # 2. Seleccionar Jugador (Solo los que jugaron esa semana)
    players = backing_service.get_players_with_activity(selected_week)
    if not players:
        st.warning("No hay actividad registrada para esta semana.")
        return
        
    player_options = {p['name']: p['id'] for p in players}
    selected_player_name = st.selectbox("Jugador", ["Seleccionar..."] + list(player_options.keys()))
    
    if selected_player_name != "Seleccionar...":
        player_id = player_options[selected_player_name]
        
        st.markdown("---")
        st.subheader(f"Liquidación para: {selected_player_name}")
        
        # Inputs de Ajuste
        c1, c2 = st.columns(2)
        bonuses = c1.number_input("Bonos / Rakeback Extra (+)", value=0.0, step=10.0)
        fees = c2.number_input("Fees / Jackpots / Seguros (-)", value=0.0, step=10.0)
        
        # PREVIEW AUTOMÁTICO
        preview = backing_service.preview_settlement(player_id, selected_week, bonuses, fees)
        
        if preview:
            # Mostrar Resumen
            st.markdown("#### 👁️ Vista Previa del Corte")
            
            # Fila 1: Bruto -> Neto
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Profit Bruto (Mesa)", f"${preview['total_gross_profit']:,.2f}")
            col2.metric("Bonos", f"+${preview['bonuses']:,.2f}")
            col3.metric("Fees", f"-${preview['fees']:,.2f}")
            col4.metric("Resultado Neto", f"${preview['net_result']:,.2f}", 
                        delta_color="normal" if preview['net_result'] >= 0 else "inverse")
            
            st.divider()
            
            # Fila 2: Distribución
            c_ply, c_club, c_debt = st.columns(3)
            c_ply.metric("💰 Para Jugador", f"${preview['player_share']:,.2f}")
            c_club.metric("🏦 Para Club/Backer", f"${preview['club_share']:,.2f}", help="Incluye recuperación de deuda")
            c_debt.metric("📉 Nueva Deuda (Makeup)", f"${preview['new_makeup']:,.2f}", 
                          delta=f"{preview['makeup_change']:,.2f} (Cambio)")
            
            # Botón Guardar
            st.write("")
            if st.button("💾 CONFIRMAR Y GUARDAR CORTE", type="primary"):
                if backing_service.save_settlement(player_id, selected_week, bonuses, fees):
                    st.success("✅ Corte guardado exitosamente. La deuda ha sido actualizada.")
                    # TODO: Podríamos mostrar historial de settlements aquí
                else:
                    st.error("Error al guardar. ¿Ya existe un corte para esta semana?")
        else:
            st.warning("⚠️ Este jugador no tiene un Deal de Backing activo. Configúralo primero en la pestaña 'Configuración'.")
