import streamlit as st
import sqlite3
from datetime import date
import os
import base64
from PIL import Image
import io

st.set_page_config(layout="wide", page_title="Control Estetica")

#FUNCION PARA CONVERTIR IMAGEN A TEXTO
def imagen_a_base64(imagen_archivo):
    if imagen_archivo is not None:
        bytes_data = imagen_archivo.getvalue()
        return base64.b64encode(bytes_data).decode()
    return None

#GESTION DE BASE DE DATOS
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
            foto_perfil TEXT
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

#INTERFAZ
st.sidebar.title("Navegacion")
opcion = st.sidebar.radio("Ir a:", ["Buscar Clienta", "Registrar Nueva Cita", "Ver Todos los Registros"])

if opcion == "Buscar Clienta":
    st.title("Expediente de Clientas")
    nombre_buscado = st.text_input("Nombre de la clienta:")
    if nombre_buscado:
        datos = ejecutar_query("SELECT * FROM HistorialEstetica WHERE nombre_clienta LIKE ? ORDER BY id_registro DESC", (f'%{nombre_buscado}%',), fetch=True)
        if datos:
            col_info, col_foto = st.columns([2, 1])
            with col_info:
                st.header(f"Ficha: {datos[1]}")
                st.write(f"Telefono: {datos[2]} | Cita: {datos[3]}")
                st.info(f"Formula: {datos[6]}")
                st.write(f"Observaciones: {datos[7]}")
            with col_foto:
                if datos[8]:
                    try:
                        st.image(f"data:image/png;base64,{datos[8]}", use_column_width=True)
                    except:
                        st.error("Error al cargar la imagen. Posible formato antiguo.")
                else:
                    st.image("https://via.placeholder.com/300?text=Sin+Foto", use_column_width=True)
        else:
            st.warning("No se encontro registro.")

elif opcion == "Registrar Nueva Cita":
    st.title("Nueva Entrada en Expediente")
    with st.form("registro", clear_on_submit=True):
        nombre = st.text_input("Nombre (Obligatorio)")
        tel = st.text_input("Telefono")
        fecha = st.date_input("Fecha de Cita", date.today())
        serv = st.selectbox("Servicio", ["Corte", "Tinte", "Peinado", "Otro"])
        formula = st.text_area("Formula Quimica")
        obs = st.text_area("Observaciones")
        foto_archivo = st.file_uploader("Foto del trabajo", type=["jpg", "png", "jpeg"])
        enviado = st.form_submit_button("Guardar Registro")
        
        if enviado and nombre:
            string_foto = imagen_a_base64(foto_archivo)
            ejecutar_query("""INSERT INTO HistorialEstetica 
                (nombre_clienta, telefono, fecha_cita, servicio, formula_tinte, observaciones, foto_perfil) 
                VALUES (?,?,?,?,?,?,?)""", (nombre, tel, str(fecha), serv, formula, obs, string_foto))
            st.success("Registro guardado con exito.")
        elif enviado and not nombre:
            st.error("El nombre de la clienta es obligatorio.")

elif opcion == "Ver Todos los Registros":
    st.title("Listado General y Administracion")
    todos = ejecutar_query("SELECT id_registro, nombre_clienta, fecha_cita, servicio FROM HistorialEstetica", fetchall=True)
    if todos:
        # Mostramos la tabla para ver los IDs
        st.table(todos)
        
        st.markdown("---")
        st.subheader("Zona de Eliminacion")
        id_borrar = st.number_input("ID del registro a eliminar:", min_value=1, step=1)
        if st.button("Eliminar Permanentemente"):
            ejecutar_query("DELETE FROM HistorialEstetica WHERE id_registro = ?", (id_borrar,))
            st.success(f"Registro {id_borrar} eliminado. Selecciona otra opcion del menu para refrescar.")
    else:
        st.write("Aun no hay registros en la base de datos.")