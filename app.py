import streamlit as st
import sqlite3
from datetime import date
import os
import base64
from PIL import Image
import io

st.set_page_config(layout="wide", page_title="Control Estetica Pro")

# FUNCION PARA CONVERTIR IMAGEN A TEXTO (BASE64)
def imagen_a_base64(imagen_archivo):
    if imagen_archivo is not None:
        bytes_data = imagen_archivo.getvalue()
        return base64.b64encode(bytes_data).decode()
    return None

# GESTION DE BASE DE DATOS
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

# INTERFAZ Y NAVEGACION
st.sidebar.title("Navegacion")
opcion = st.sidebar.radio("Ir a:", ["Buscar Clienta", "Registrar Nueva Cita", "Ver Todos los Registros"])

# --- BUSCAR CON FILTRO DOBLE ---
if opcion == "Buscar Clienta":
    st.title("Expediente de Clientas")
    
    col_bus1, col_bus2 = st.columns(2)
    with col_bus1:
        nombre_buscado = st.text_input("Buscar por Nombre:")
    with col_bus2:
        tel_buscado = st.text_input("Buscar por Telefono:")
    
    if nombre_buscado or tel_buscado:
        query = """
            SELECT * FROM HistorialEstetica 
            WHERE nombre_clienta LIKE ? AND telefono LIKE ? 
            ORDER BY id_registro DESC
        """
        params = (f'%{nombre_buscado}%', f'%{tel_buscado}%')
        datos = ejecutar_query(query, params, fetch=True)
        
        if datos:
            st.markdown("---")
            col_info, col_foto = st.columns([2, 1])
            
            with col_info:
                st.header(f"Ficha: {datos[1]}")
                st.write(f"Telefono: {datos[2]}")
                st.write(f"Ultima Cita: {datos[3]}")
                st.write(f"Atendida por: {datos[4]}")
                st.write(f"Servicio: {datos[5]}")
                st.info(f"Formula: {datos[6] if datos[6] else 'Sin registro'}")
                st.write(f"Observaciones: {datos[7] if datos[7] else 'Ninguna'}")
            
            with col_foto:
                if datos[8]:
                    st.image(f"data:image/png;base64,{datos[8]}", use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/300?text=Sin+Foto", use_column_width=True)
        else:
            st.warning("No se encontro ningun registro que coincida.")

# --- REGISTRAR ---
elif opcion == "Registrar Nueva Cita":
    st.title("Nueva Entrada en Expediente")
    with st.form("registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre de la Clienta (Obligatorio)")
            tel = st.text_input("Telefono")
            fecha = st.date_input("Fecha de Cita", date.today())
        with col2:
            estilista = st.text_input("Estilista")
            serv = st.selectbox("Servicio", ["Corte", "Tinte", "Peinado", "Tratamiento", "B.Color", "Efecto", "Retoque", "C.Global", "Otro"])
        
        formula = st.text_area("Formula Quimica")
        obs = st.text_area("Observaciones o Alergias")
        foto_archivo = st.file_uploader("Foto del trabajo", type=["jpg", "png", "jpeg"])
        
        enviado = st.form_submit_button("Guardar Registro")
        
        if enviado and nombre:
            string_foto = imagen_a_base64(foto_archivo)
            ejecutar_query("""INSERT INTO HistorialEstetica 
                (nombre_clienta, telefono, fecha_cita, estilista, servicio, formula_tinte, observaciones, foto_perfil) 
                VALUES (?,?,?,?,?,?,?,?)""", (nombre, tel, str(fecha), estilista, serv, formula, obs, string_foto))
            st.success("Registro guardado con exito.")
        elif enviado and not nombre:
            st.error("Error: El nombre es obligatorio.")

#--- ADMINISTRACION CON REORDENAMIENTO ---
elif opcion == "Ver Todos los Registros":
    st.title("Listado General y Administracion")
    todos = ejecutar_query("SELECT id_registro, nombre_clienta, telefono, fecha_cita FROM HistorialEstetica", fetchall=True)
    
    if todos:
        st.table(todos)
        st.markdown("---")
        st.subheader("Zona de Eliminacion")
        id_borrar = st.number_input("ID del registro a eliminar:", min_value=1, step=1)
        
        if st.button("Eliminar y Reordenar"):
            ejecutar_query("DELETE FROM HistorialEstetica WHERE id_registro = ?", (id_borrar,))
            ejecutar_query("UPDATE HistorialEstetica SET id_registro = id_registro - 1 WHERE id_registro > ?", (id_borrar,))
            
            max_id_res = ejecutar_query("SELECT MAX(id_registro) FROM HistorialEstetica", fetch=True)
            nuevo_conteo = max_id_res[0] if max_id_res[0] is not None else 0
            ejecutar_query("UPDATE sqlite_sequence SET seq = ? WHERE name = 'HistorialEstetica'", (nuevo_conteo,))
            
            st.success(f"Registro {id_borrar} eliminado y base de datos reordenada.")
            st.rerun()
    else:
        st.write("No hay registros en la base de datos.")