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

# --- BUSCAR SOLO POR NOMBRE ---
if opcion == "Buscar y Ver Historial":
    st.title("Expediente de Clientas")
    nom_b = st.text_input("Escribe el nombre de la clienta para buscar su ficha:")
    
    if nom_b:
        cliente = ejecutar_query("SELECT * FROM Clientes WHERE nombre LIKE ?", (f'%{nom_b}%',), fetch=True)
        
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
                st.write("No hay visitas registradas en el historial.")
        else:
            st.warning("No se encontro ninguna clienta con ese nombre.")

# --- REGISTRAR VISITA (Deteccion por Nombre) ---
elif opcion == "Registrar Visita":
    st.title("Registrar Nueva Visita")
    nombre_input = st.text_input("Escribe el nombre de la clienta:")
    
    if nombre_input:
        existe = ejecutar_query("SELECT id_cliente, telefono FROM Clientes WHERE nombre = ?", (nombre_input,), fetch=True)
        
        with st.form("form_registro", clear_on_submit=True):
            if existe:
                st.success(f"Cliente reconocido: {nombre_input}. Telefono: {existe[1]}")
                telefono = existe[1]
                foto_up = None
            else:
                st.info("Nueva clienta detectada.")
                telefono = st.text_input("Telefono:")
                foto_up = st.file_uploader("Foto de Perfil", type=["jpg", "png", "jpeg"])

            col_a, col_b = st.columns(2)
            with col_a:
                fecha = st.date_input("Fecha", date.today())
                estilista = st.text_input("Estilista")
            with col_b:
                serv = st.selectbox("Servicio", ["Corte", "Tinte", "Peinado", "Tratamiento", "B.Color", "Efecto", "Retoque", "C.Global", "Otro"])
            
            formula = st.text_area("Formula")
            obs = st.text_area("Observaciones")
            
            if st.form_submit_button("Guardar en Expediente"):
                if existe:
                    id_c = existe[0]
                else:
                    if nombre_input and telefono:
                        img_str = imagen_a_base64(foto_up)
                        id_c = ejecutar_query("INSERT INTO Clientes (nombre, telefono, foto_perfil) VALUES (?,?,?)", (nombre_input, telefono, img_str), return_id=True)
                    else:
                        st.error("Error: Nombre y Telefono son obligatorios para nuevas clientas.")
                        st.stop()
                
                ejecutar_query("INSERT INTO Visitas (id_cliente, fecha, estilista, servicio, formula, observaciones) VALUES (?,?,?,?,?,?)", 
                               (id_c, str(fecha), estilista, serv, formula, obs))
                st.success("Guardado correctamente en el historial.")
    else:
        st.write("Ingresa un nombre arriba para comenzar.")

# --- ADMINISTRACION (BORRADO CON REORDENAMIENTO) ---
elif opcion == "Administrar Sistema":
    st.title("Panel de Administracion")
    clientes = ejecutar_query("SELECT id_cliente, nombre, telefono FROM Clientes", fetchall=True)
    if clientes:
        st.table(clientes)
        st.markdown("---")
        id_borrar = st.number_input("ID de clienta para eliminar:", min_value=1, step=1)
        if st.button("Eliminar Permanentemente"):
            ejecutar_query("DELETE FROM Visitas WHERE id_cliente = ?", (id_borrar,))
            ejecutar_query("DELETE FROM Clientes WHERE id_cliente = ?", (id_borrar,))
            ejecutar_query("UPDATE Visitas SET id_cliente = id_cliente - 1 WHERE id_cliente > ?", (id_borrar,))
            ejecutar_query("UPDATE Clientes SET id_cliente = id_cliente - 1 WHERE id_cliente > ?", (id_borrar,))
            max_id = ejecutar_query("SELECT MAX(id_cliente) FROM Clientes", fetch=True)[0]
            ejecutar_query("UPDATE sqlite_sequence SET seq = ? WHERE name = 'Clientes'", (max_id if max_id else 0,))
            st.success("Expediente eliminado y IDs reajustados.")
            st.rerun()
    else:
        st.write("No hay clientas registradas.")