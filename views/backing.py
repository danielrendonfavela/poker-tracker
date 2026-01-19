import streamlit as st
import pandas as pd
from services import player_service, backing_service, report_service

def render_view():
    st.title("🤝 Sistema de Backing")
    
    tab1, tab2 = st.tabs(["⚙️ Configuración", "📊 Estado de Cuenta"])
    
    with tab1:
        render_config_tab()
    
    with tab2:
        render_status_tab()

def render_config_tab():
    st.header("Configurar Deal")
    
    players = player_service.get_all_players_dict()
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_player = st.selectbox("Seleccionar Jugador", ["Seleccionar..."] + list(players.keys()))
    
    with col2:
        deal_pct = st.number_input("Porcentaje Jugador (%)", min_value=0, max_value=100, value=50, step=5)
    
    if selected_player != "Seleccionar...":
        player_id = players[selected_player]
        current_deal = backing_service.get_active_deal(player_id)
        
        if current_deal:
            st.info(f"ℹ️ Este jugador ya tiene un deal activo del **{current_deal['deal_percentage']*100:.0f}%**. Al guardar se actualizará.")
        
        if st.button("Guardar Deal"):
            # Convertir a decimal (50 -> 0.5)
            pct_decimal = deal_pct / 100.0
            if backing_service.create_or_update_deal(player_id, pct_decimal):
                st.success(f"Deal creado para {selected_player} al {deal_pct}%")
                st.rerun()

def render_status_tab():
    st.header("Estado de Jugadores con Backing")
    
    deals = backing_service.get_all_deals_status()
    
    if not deals:
        st.info("No hay jugadores con deals activos.")
        return
    
    # Preparamos datos para la tabla
    data = []
    
    # Cargar datos financieros generales (esto podría optimizarse luego)
    # Por ahora, calcularemos un estimado basado en TODOS los registros históricos del jugador
    # OJO: En un sistema real, el backing empieza desde cierta fecha. 
    # Para este MVP, asumiremos que se calcula sobre el total histórico si no hay fecha de inicio,
    # O mejor aún: Mostramos el Makeup Actual que viene de la DB y una simulación de la última semana.
    
    last_week_stats = report_service.load_week_details(week="30/Oct/2025 - 05/Nov/2025") # TODO: Get real last week dynamically
    # Para simplificar el MVP, mostraremos solo la tabla de Makeup Actual
    
    for deal in deals:
        data.append({
            "Jugador": deal['player'],
            "Deal %": f"{deal['deal_percentage']*100:.0f}%",
            "Makeup (Deuda)": deal['current_makeup']
        })
        
    df = pd.DataFrame(data)
    
    # Formato condicional para Makeup (Rojo si > 0)
    st.dataframe(
        df.style.format({
            "Makeup (Deuda)": "${:,.2f}"
        }).applymap(lambda v: 'color: red; font-weight: bold' if v > 0 else '', subset=['Makeup (Deuda)']),
        use_container_width=True
    )
    
    st.markdown("---")
    st.subheader("🔍 Simuador de Cálculo (Prueba)")
    st.caption("Usa esto para verificar cómo se distribuiría una ganancia/pérdida hipotética.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        sim_profit = st.number_input("Profit de la Semana", value=0.0, step=100.0)
    with c2:
        sim_deal = st.number_input("Deal %", value=50) / 100.0
    with c3:
        sim_makeup = st.number_input("Makeup Inicial", value=1000.0, step=100.0)
        
    if st.button("Calcular Distribución"):
        result = backing_service.calculate_weekly_share(sim_profit, sim_deal, sim_makeup)
        
        r1, r2, r3, r4 = st.columns(4)
        r1.metric(
            "Para Jugador", 
            f"${result['player_share']:,.2f}",
            help="Dinero libre para el jugador (Ganancia - Deuda Pagada - % Club)."
        )
        r2.metric(
            "Para Club/Backer", 
            f"${result['club_share']:,.2f}",
            help="Total para el Backer (Su % de Ganancia + Deuda Recuperada)."
        )
        r3.metric(
            "Cambio en Deuda", 
            f"${result['makeup_change']:,.2f}",
            help="Cómo cambió la deuda: Negativo (-) significa que se pagó deuda, Positivo (+) que aumentó."
        )
        r4.metric(
            "Nueva Deuda", 
            f"${result['new_makeup']:,.2f}",
            help="Deuda total acumulada (Makeup) para la siguiente semana."
        )
