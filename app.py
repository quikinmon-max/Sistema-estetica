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

# GESTION DE BASE DE DATOS
def inicializar_db():
    conn = sqlite3.connect('estetica_pro.db')
    cursor = conn.cursor()
    # TABLA DE CLIENTAS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Clientes (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            telefono TEXT,
            foto_perfil TEXT
        )
    """)
    # TABLA DE VISITAS
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

def ejecutar_query(query, params=(), fetch=False, fetchall=False, return_id=False):
    conn = sqlite3.connect('estetica_pro.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    if return_id:
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id
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
opcion = st.sidebar.radio("Ir a:", ["Buscar y Ver Historial", "Registrar Visita", "Administrar Sistema"])

# --- BUSCAR Y VER HISTORIAL (ORDEN ANTIGUO A NUEVO) ---
if opcion == "Buscar y Ver Historial":
    st.title("Expediente de Clientas")
    
    c1, c2 = st.columns(2)
    with c1:
        nom_b = st.text_input("Buscar por Nombre:")
    with c2:
        tel_b = st.text_input("Buscar por Telefono:")

    if nom_b or tel_b:
        cliente = ejecutar_query("SELECT * FROM Clientes WHERE nombre LIKE ? AND telefono LIKE ?", (f'%{nom_b}%', f'%{tel_b}%'), fetch=True)
        
        if cliente:
            st.markdown("---")
            col_info, col_foto = st.columns([2, 1])
            with col_info:
                st.header(f"Clienta: {cliente[1]}")
                st.write(f"Telefono: {cliente[2]}")
            with col_foto:
                if cliente[3]:
                    st.image(f"data:image/png;base64,{cliente[3]}", width=300)
                else:
                    st.image("https://via.placeholder.com/300?text=Sin+Foto")

            st.subheader("Historial de Visitas")
            visitas = ejecutar_query("SELECT fecha, servicio, formula, observaciones, estilista FROM Visitas WHERE id_cliente = ? ORDER BY fecha ASC", (cliente[0],), fetchall=True)
            
            if visitas:
                for v in visitas:
                    with st.expander(f"Fecha: {v[0]} - Servicio: {v[1]}"):
                        st.write(f"Atendida por: {v[4]}")
                        st.info(f"Formula: {v[2]}")
                        st.write(f"Observaciones: {v[3]}")
            else:
                st.write("Aun no hay visitas registradas.")
        else:
            st.warning("No se encontro a la clienta.")

# --- REGISTRAR VISITA ---
elif opcion == "Registrar Visita":
    st.title("Registrar Nueva Visita")
    nombre = st.text_input("Nombre de la Clienta (Obligatorio)")
    telefono = st.text_input("Telefono (Obligatorio)")
    
    existe = ejecutar_query("SELECT id_cliente, foto_perfil FROM Clientes WHERE nombre = ? AND telefono = ?", (nombre, telefono), fetch=True)
    
    with st.form("form_registro", clear_on_submit=True):
        if not existe:
            st.info("Nueva clienta detectada.")
            foto_up = st.file_uploader("Foto de Perfil", type=["jpg", "png", "jpeg"])
        else:
            st.success("Clienta reconocida.")
            foto_up = None

        col_a, col_b = st.columns(2)
        with col_a:
            fecha = st.date_input("Fecha", date.today())
            estilista = st.text_input("Estilista")
        with col_b:
            serv = st.selectbox("Servicio", ["Corte", "Tinte", "Peinado", "Tratamiento", "B.Color", "Efecto", "Retoque", "C.Global", "Otro"])
        
        formula = st.text_area("Formula")
        obs = st.text_area("Observaciones")
        
        btn_guardar = st.form_submit_button("Guardar en Expediente")
        
        if btn_guardar and nombre and telefono:
            if not existe:
                img_str = imagen_a_base64(foto_up)
                id_c = ejecutar_query("INSERT INTO Clientes (nombre, telefono, foto_perfil) VALUES (?,?,?)", (nombre, telefono, img_str), return_id=True)
            else:
                id_c = existe[0]
            
            ejecutar_query("""INSERT INTO Visitas (id_cliente, fecha, estilista, servicio, formula, observaciones) 
                           VALUES (?,?,?,?,?,?)""", (id_c, str(fecha), estilista, serv, formula, obs))
            st.success("Registro completado con exito.")

# --- ADMINISTRACION ---
elif opcion == "Administrar Sistema":
    st.title("Panel de Administracion")
    clientes = ejecutar_query("SELECT id_cliente, nombre, telefono FROM Clientes", fetchall=True)
    if clientes:
        st.write("Lista de clientas activas:")
        st.table(clientes)
        st.markdown("---")
        id_borrar = st.number_input("ID de clienta para borrar (Se reordenaran los IDs):", min_value=1, step=1)
        
        if st.button("Eliminar Permanentemente"):

            ejecutar_query("DELETE FROM Visitas WHERE id_cliente = ?", (id_borrar,))
            ejecutar_query("DELETE FROM Clientes WHERE id_cliente = ?", (id_borrar,))
            ejecutar_query("UPDATE Visitas SET id_cliente = id_cliente - 1 WHERE id_cliente > ?", (id_borrar,))
            ejecutar_query("UPDATE Clientes SET id_cliente = id_cliente - 1 WHERE id_cliente > ?", (id_borrar,))
            
            max_id_res = ejecutar_query("SELECT MAX(id_cliente) FROM Clientes", fetch=True)
            nuevo_conteo = max_id_res[0] if max_id_res[0] is not None else 0
            ejecutar_query("UPDATE sqlite_sequence SET seq = ? WHERE name = 'Clientes'", (nuevo_conteo,))
            
            st.success(f"Clienta con ID {id_borrar} eliminada. Los IDs se han reajustado.")
            st.rerun()
    else:
        st.write("No hay clientas en el sistema.")