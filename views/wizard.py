import streamlit as st
import services.config_service as config_service
import time

def render_wizard():
    st.markdown("""
        <style>
        .wizard-container {
            max-width: 600px;
            margin: auto;
            padding: 2rem;
            border-radius: 10px;
            background-color: #f8f9fa;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton>button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("♠️ Poker Tracker")
        st.markdown("### Asistente de Configuración")
        st.write("Bienvenido. Configuremos tu club para empezar.")
        
        with st.form("wizard_form", clear_on_submit=False):
            st.subheader("1. Detalles del Club")
            club_name = st.text_input("Nombre del Club Principal", placeholder="Ej: Club Patos MX")
            
            st.subheader("2. Administrador")
            admin_name = st.text_input("Tu Nombre (Admin)", placeholder="Ej: Daniel")
            
            st.subheader("3. Preferencias")
            currency = st.selectbox("Divisa Principal", ["MXN", "USD", "EUR"])
            
            st.write("")
            submitted = st.form_submit_button("🚀 Iniciar Aplicación", type="primary")
            
            if submitted:
                if club_name and admin_name:
                    with st.spinner("Configurando base de datos..."):
                        success = config_service.initialize_app(
                            club_name=club_name,
                            admin_name=admin_name,
                            currency=currency
                        )
                        
                        if success:
                            st.toast("✅ ¡Configuración exitosa!", icon="🚀")
                            time.sleep(1.0)
                            st.rerun()
                        else:
                            st.error("Hubo un error al guardar la configuración.")
                else:
                    st.warning("⚠️ El nombre del club y el administrador son obligatorios.")
        
        st.caption("Esta configuración solo se realiza una vez.")
