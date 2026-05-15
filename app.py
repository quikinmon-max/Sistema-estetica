import streamlit as st
import sqlite3
from datetime import date
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

# GESTION DE BASE DE DATOS (SISTEMA DE DOS TABLAS)
def inicializar_db():
    conn = sqlite3.connect('estetica_pro.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Clientes (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            telefono TEXT,
            foto_perfil TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Visitas (
            id_visita INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER,
            fecha TEXT,
            estilista TEXT,
            servicio TEXT,
            formula TEXT,
            observaciones TEXT,
            FOREIGN KEY(id_cliente) REFERENCES Clientes(id_cliente)
        )
    """)
    conn.commit()
    conn.close()

def ejecutar_query(query, params=(), fetch=False, fetchall=False):
    conn = sqlite3.connect('estetica_pro.db')
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

# NAVEGACION
st.sidebar.title("Navegacion")
opcion = st.sidebar.radio("Ir a:", ["Buscar y Ver Historial", "Registrar Visita", "Lista de Clientes"])

# --- BUSCAR Y VER HISTORIAL ---
if opcion == "Buscar y Ver Historial":
    st.title("Expediente Unificado")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        nom_b = st.text_input("Buscar por Nombre:")
    with col_b2:
        tel_b = st.text_input("Buscar por Telefono:")

    if nom_b or tel_b:
        cliente = ejecutar_query("SELECT * FROM Clientes WHERE nombre LIKE ? AND telefono LIKE ?", (f'%{nom_b}%', f'%{tel_b}%'), fetch=True)
        
        if cliente:
            st.markdown("---")
            c_perfil, c_foto = st.columns([2, 1])
            with c_perfil:
                st.header(f"Clienta: {cliente[1]}")
                st.write(f"Telefono: {cliente[2]}")
            with c_foto:
                if cliente[3]:
                    st.image(f"data:image/png;base64,{cliente[3]}", width=200)
                else:
                    st.image("https://via.placeholder.com/200?text=Sin+Foto")

            st.subheader("Historial de Visitas")
            visitas = ejecutar_query("SELECT fecha, servicio, formula, observaciones, estilista FROM Visitas WHERE id_cliente = ? ORDER BY fecha DESC", (cliente[0],), fetchall=True)
            
            if visitas:
                for v in visitas:
                    with st.expander(f"Fecha: {v[0]} - Servicio: {v[1]}"):
                        st.write(f"Atendida por: {v[4]}")
                        st.info(f"Formula: {v[2]}")
                        st.write(f"Observaciones: {v[3]}")
            else:
                st.write("Esta clienta aun no tiene visitas registradas.")
        else:
            st.warning("No se encontro ninguna clienta con esos datos.")

# --- REGISTRAR VISITA (CON LA LINEA NUEVA) ---
elif opcion == "Registrar Visita":
    st.title("Registrar Nueva Visita")
    
    nombre = st.text_input("Nombre de la Clienta (Obligatorio)")
    telefono = st.text_input("Telefono (Obligatorio)")
    existe = ejecutar_query("SELECT id_cliente, foto_perfil FROM Clientes WHERE nombre = ? AND telefono = ?", (nombre, telefono), fetch=True)
    
    with st.form("form_visita", clear_on_submit=True):
        if not existe:
            st.info("Nueva clienta detectada. Por favor sube una foto de perfil.")
            foto_nueva = st.file_uploader("Foto de Perfil", type=["jpg", "png", "jpeg"])
        else:
            st.success("Clienta reconocida. No es necesario subir la foto de nuevo.")
            foto_nueva = None

        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha de la visita", date.today())
            estilista = st.text_input("Estilista que atendio")
        with col2:
            serv = st.selectbox("Servicio", ["Corte", "Tinte", "Peinado", "Tratamiento", "B.Color", "Efecto", "Retoque", "C.Global", "Otro"])
        
        formula = st.text_area("Formula aplicada")
        obs = st.text_area("Observaciones adicionales")
        
        guardar = st.form_submit_button("Guardar en Historial")
        
        if guardar and nombre and telefono:
            if not existe:
                img_b64 = imagen_a_base64(foto_nueva)
                ejecutar_query("INSERT INTO Clientes (nombre, telefono, foto_perfil) VALUES (?,?,?)", (nombre, telefono, img_b64))
                id_c = ejecutar_query("SELECT last_insert_rowid()", fetch=True)[0]
            else:
                id_c = existe[0]
            
            ejecutar_query("""INSERT INTO Visitas (id_cliente, fecha, estilista, servicio, formula, observaciones) 
                           VALUES (?,?,?,?,?,?)""", (id_c, str(fecha), estilista, serv, formula, obs))
            st.success("La visita se ha guardado correctamente en el expediente.")
        elif guardar:
            st.error("El nombre y el telefono son obligatorios para el registro.")

# --- LISTA DE CLIENTES ---
elif opcion == "Lista de Clientes":
    st.title("Directorio General")
    clientes = ejecutar_query("SELECT id_cliente, nombre, telefono FROM Clientes", fetchall=True)
    if clientes:
        st.write("Esta es la lista de clientas unicas registradas:")
        st.table(clientes)
    else:
        st.write("Aun no hay clientas registradas en el sistema.")