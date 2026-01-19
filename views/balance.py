import streamlit as st
import pandas as pd
import plotly.express as px
from services.report_service import get_available_weeks
from services.database import get_connection

def render_view():
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
