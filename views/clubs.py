import streamlit as st
from services.club_service import load_club_summary

def render_view():
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
                "balance": st.column_config.NumberColumn("Balance", format="$%.2f"),
            }
        )
    else:
        st.warning("No hay clubes registrados.")
