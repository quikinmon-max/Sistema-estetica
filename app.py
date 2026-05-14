import streamlit as st
import sqlite3
from datetime import date
import os
import base64
from PIL import Image
import io

st.set_page_config(layout="wide", page_title="Control Estética")

# FUNCIÓN PARA CONVERTIR IMAGEN A TEXTO (Base64)
def imagen_a_base64(imagen_archivo):
    if imagen_archivo is not None:
        bytes_data = imagen_archivo.getvalue()
        return base64.b64encode(bytes_data).decode()
    return None

# GESTIÓN DE BASE DE DATOS
def inicializar_db():
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
            foto_perfil TEXT -- Aquí guardaremos el texto de la imagen
        )
    """)
    conn.commit()
    conn.close()

def ejecutar_query(query, params=(), fetch=False, fetchall=False):
    conn = sqlite3.connect('estetica.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetchall:
        res = cursor.fetchall()
        conn.close()
        return res
    if fetch:
        res = cursor.fetchone()
        conn.close()
        return res
    conn.commit()
    conn.close()

inicializar_db()

# INTERFAZ
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Ir a:", ["Buscar Clienta", "Registrar Nueva Cita", "Ver Todos los Registros"])

if opcion == "Buscar Clienta":
    st.title("Expediente")
    nombre_buscado = st.text_input("Nombre:")
    if nombre_buscado:
        datos = ejecutar_query("SELECT * FROM HistorialEstetica WHERE nombre_clienta LIKE ? ORDER BY id_registro DESC", (f'%{nombre_buscado}%',), fetch=True)
        if datos:
            col_info, col_foto = st.columns([2, 1])
            with col_info:
                st.header(f"Ficha: {datos[1]}")
                st.write(f"**Teléfono:** {datos[2]} | **Cita:** {datos[3]}")
                st.info(f"Fórmula: {datos[6]}")
            with col_foto:
                if datos[8]:
                    st.image(f"data:image/png;base64,{datos[8]}", use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/300?text=Sin+Foto", use_column_width=True)
        else:
            st.warning("No se encontró.")

elif opcion == "Registrar Nueva Cita":
    st.title("Nueva Cita")
    with st.form("registro"):
        nombre = st.text_input("Nombre *")
        formula = st.text_area("Fórmula")
        foto_archivo = st.file_uploader("Foto", type=["jpg", "png", "jpeg"])
        enviado = st.form_submit_button("Guardar")
        
        if enviado and nombre:
            string_foto = imagen_a_base64(foto_archivo)
            ejecutar_query("INSERT INTO HistorialEstetica (nombre_clienta, formula_tinte, foto_perfil) VALUES (?,?,?)", 
                           (nombre, formula, string_foto))
            st.success("¡Guardado!")

elif opcion == "Ver Todos los Registros":
    st.title("Listado General")
    todos = ejecutar_query("SELECT id_registro, nombre_clienta, fecha_cita, servicio FROM HistorialEstetica", fetchall=True)
    if todos:
        st.table(todos)
    else:
        st.write("No hay registros todavía.")