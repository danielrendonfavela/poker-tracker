import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.player_service import add_player, add_nickname_mapping, load_players, get_all_players_dict
from services.club_service import load_clubs, get_club_id
from services.report_service import add_weekly_record, add_multiple_weekly_records

def render_view():
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
