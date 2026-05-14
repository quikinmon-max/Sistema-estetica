import streamlit as st
import sqlite3
from datetime import date
import os

st.set_page_config(layout="wide", page_title="Control Estética")

if not os.path.exists("fotos"):
    os.makedirs("fotos")

def inicializar_db():
    """Crea la tabla si no existe para evitar errores de 'no existe tal tabla'."""
    conn = sqlite3.connect('estetica.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS HistorialEstetica (
            id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_clienta TEXT,
            telefono TEXT,
            fecha_cita TEXT,
            estilista TEXT,
            servicio TEXT,
            formula_tinte TEXT,
            observaciones TEXT,
            foto_perfil TEXT
        )
    """)
    conn.commit()
    conn.close()

def ejecutar_query(query, params=(), fetch=False):
    conn = sqlite3.connect('estetica.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        res = cursor.fetchone()
        conn.close()
        return res
    conn.commit()
    conn.close()

inicializar_db()

st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Ir a:", ["🔍 Buscar Clienta", "Registrar Nueva Cita"])

if opcion == "Buscar Clienta":
    st.title("Expediente de Clientas")
    nombre_buscado = st.text_input("Ingrese nombre de la clienta:")
    
    if nombre_buscado:
        datos = ejecutar_query(
            "SELECT * FROM HistorialEstetica WHERE nombre_clienta LIKE ? ORDER BY id_registro DESC", 
            (f'%{nombre_buscado}%',), 
            fetch=True
        )
        
        if datos:
            st.markdown("---")
            col_info, col_foto = st.columns([2, 1])
            
            with col_info:
                st.header(f"Ficha: {datos[1]}")
                st.write(f"**Teléfono:** {datos[2]}")
                st.write(f"**Última Cita:** {datos[3]}")
                st.write(f"**Atendida por:** {datos[4]}")
                st.write(f"**Servicio:** {datos[5]}")
                
                st.subheader("🧪 Fórmula de Color")
                st.info(datos[6] if datos[6] else "Sin fórmula registrada.")
                
                st.subheader("Observaciones")
                st.write(datos[7] if datos[7] else "Ninguna.")
            
            with col_foto:
                # Ajuste de 'use_column_width' para versiones estables
                if datos[8] and os.path.exists(datos[8]):
                    st.image(datos[8], caption="Foto del último servicio", use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/300?text=Sin+Foto", use_column_width=True)
        else:
            st.warning("No se encontró ningún registro.")

elif opcion == "Registrar Nueva Cita":
    st.title("Nueva Entrada en Expediente")
    
    with st.form("registro_cita", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre de la Clienta *")
            tel = st.text_input("Teléfono")
            fecha = st.date_input("Fecha", date.today())
        with col2:
            estilista = st.text_input("Estilista responsable")
            servicio = st.selectbox("Servicio", ["Corte", "Tinte/Color", "Peinado", "Tratamiento", "Otro"])
        
        formula = st.text_area("Fórmula Química")
        obs = st.text_area("Observaciones/Alergias")
        foto_archivo = st.file_uploader("Capturar o subir foto", type=["jpg", "png", "jpeg"])
        
        enviado = st.form_submit_button("Guardar en Expediente")

    if enviado:
        if nombre:
            ruta_foto = ""
            if foto_archivo is not None:
                nombre_archivo = f"{nombre.replace(' ', '_')}_{foto_archivo.name}"
                ruta_foto = os.path.join("fotos", nombre_archivo)
                with open(ruta_foto, "wb") as f:
                    f.write(foto_archivo.getbuffer())
            
            ejecutar_query("""
                INSERT INTO HistorialEstetica 
                (nombre_clienta, telefono, fecha_cita, estilista, servicio, formula_tinte, observaciones, foto_perfil) 
                VALUES (?,?,?,?,?,?,?,?)
            """, (nombre, tel, str(fecha), estilista, servicio, formula, obs, ruta_foto))
            
            st.success(f"¡Expediente de {nombre} guardado!")
            st.balloons()
        else:
            st.error("El nombre es obligatorio.")