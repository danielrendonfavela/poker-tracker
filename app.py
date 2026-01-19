import streamlit as st
import pandas as pd
import sqlite3
import os

# Configuración de página
st.set_page_config(
    page_title="Poker Tracker",
    page_icon="♠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Importar vistas
from views import dashboard, players, clubs, weekly, balance, records, data_entry

def main():
    # Sidebar
    st.sidebar.title("♠️ Poker Tracker")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navegación",
        ["🏠 Dashboard", "👥 Jugadores", "🏢 Clubes", "📅 Por Semana", "💰 Balance", "📝 Registros", "➕ Agregar Datos"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("v2.0.0 (Modular)")

    # Enrutador
    if page == "🏠 Dashboard":
        dashboard.render_view()
    elif page == "👥 Jugadores":
        players.render_view()
    elif page == "🏢 Clubes":
        clubs.render_view()
    elif page == "📅 Por Semana":
        weekly.render_view()
    elif page == "💰 Balance":
        balance.render_view()
    elif page == "📝 Registros":
        records.render_view()
    elif page == "➕ Agregar Datos":
        data_entry.render_view()

if __name__ == "__main__":
    main()
