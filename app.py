import streamlit as st
import google.generativeai as genai
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Asistente Redfil", page_icon="🚗")

# --- GESTIÓN DE CONTRASEÑA ---
def check_password():
    """Retorna `True` si el usuario tiene la clave correcta."""
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Borrar clave por seguridad
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primera vez, mostrar input
        st.text_input(
            "🔑 Ingrese la clave de acceso:", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Clave incorrecta
        st.text_input(
            "🔑 Ingrese la clave de acceso:", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Clave incorrecta")
        return False
    else:
        # Clave correcta
        return True

if check_password():
    # --- AQUÍ COMIENZA LA APLICACIÓN SI LA CLAVE ES CORRECTA ---
    
    # Configurar API Key (se toma de los secretos de la nube)
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

    st.title("🤖 Agente Experto Redfil")
    st.markdown("Pregúntame sobre filtros, modelos de vehículos o medidas del catálogo.")

    # Cargar el archivo PDF (El archivo debe estar en la misma carpeta del código)
    pdf_path = "CATALOGO REDFIL ACTUALIZADO-2.pdf"

    # Función para subir el archivo a Gemini (Caché temporal)
    @st.cache_resource
    def upload_to_gemini(path):
        """Sube el archivo a Gemini una sola vez para ahorrar recursos."""
        try:
            file = genai.upload_file(path, mime_type="application/pdf")
            return file
        except Exception as e:
            st.error(f"Error al cargar el catálogo: {e}")
            return None

    if os.path.exists(pdf_path):
        catalog_file = upload_to_gemini(pdf_path)
        
        if catalog_file:
            # Configurar el modelo
            generation_config = {
                "temperature": 0.2, # Bajo para ser preciso con los datos
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
            }
            
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                system_instruction="Eres un experto en autopartes. Tu única fuente de verdad es el archivo PDF adjunto. Responde consultas sobre códigos de filtros, aplicaciones vehiculares y medidas. Si no encuentras el dato en el archivo, di 'No figura en el catálogo'."
            )

            # Chat Interface
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Ej: ¿Qué filtro de aire usa el Chevrolet Corsa?"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Buscando en el catálogo..."):
                        try:
                            # Enviamos el archivo y la pregunta
                            response = model.generate_content([catalog_file, prompt])
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"Error en la consulta: {e}")
    else:
        st.warning("⚠️ No se encontró el archivo 'CATALOGO REDFIL ACTUALIZADO-2.pdf' en el directorio.")