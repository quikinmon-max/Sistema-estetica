import streamlit as st
from datetime import date
import base64
from PIL import Image
import io
import pandas as pd
from pymongo import MongoClient
from bson.objectid import ObjectId

st.set_page_config(layout="wide", page_title="Control Estetica Pro")

# 1. CONEXION A MONGO DB ATLAS
# Usamos st.secrets para proteger tus credenciales en la nube
@st.cache_resource
def obtener_conexion_mongo():
    try:
        # Reemplaza la URI en los Secrets de Streamlit con la tuya de Atlas
        mongo_uri = st.secrets["mongo"]["uri"]
        client = MongoClient(mongo_uri)
        # Creamos o conectamos a la base de datos "control_negocios"
        db = client["control_negocios"]
        return db
    except Exception as e:
        st.error(f"Error de conexion a MongoDB: {e}")
        return None

db = obtener_conexion_mongo()

# 2. FUNCION PARA ENCOGER Y CONVERTIR IMAGEN (Evita sobrecargar la BD)
def imagen_a_base64(imagen_archivo):
    if imagen_archivo is not None:
        try:
            img = Image.open(imagen_archivo)
            img.thumbnail((300, 300))
            buffered = io.BytesIO()
            img.save(buffered, format="PNG", optimize=True)
            return base64.b64encode(buffered.getvalue()).decode()
        except Exception:
            return None
    return None

# 3. NAVEGACION
st.sidebar.title("Navegacion")
opcion = st.sidebar.radio("Ir a:", ["Buscar y Ver Historial", "Registrar Visita", "Administrar Sistema"])

if db is None:
    st.error("No se pudo establecer comunicacion con la base de datos en la nube.")
else:
    # Definimos nuestras colecciones (Equivalente a tablas)
    clientes_col = db["clientes"]
    visitas_col = db["visitas"]

    # --- SECCION 1: BUSCAR POR NOMBRE ---
    if opcion == "Buscar y Ver Historial":
        st.title("Expediente de Clientas")
        nom_b = st.text_input("Escribe el nombre de la clienta:")
        
        if nom_b:
            # Busqueda insensible a mayusculas/minusculas usando regex de Mongo
            cliente = clientes_col.find_one({"nombre": {"$regex": nom_b, "$options": "i"}})
            
            if cliente:
                st.markdown("---")
                col_info, col_foto = st.columns([2, 1])
                with col_info:
                    st.header(f"Clienta: {cliente['nombre']}")
                    st.write(f"Telefono: {cliente['telefono']}")
                with col_foto:
                    if "foto_perfil" in cliente and cliente["foto_perfil"]:
                        try:
                            st.image(f"data:image/png;base64,{cliente['foto_perfil']}", width=250)
                        except:
                            st.error("Error al mostrar la foto.")
                    else:
                        st.image("https://via.placeholder.com/250?text=Sin+Foto")

                st.subheader("Historial de Visitas")
                # Filtramos las visitas ligadas al ID del cliente y ordenamos por fecha ascendente (1)
                visitas = list(visitas_col.find({"id_cliente": cliente["_id"]}).sort("fecha", 1))
                
                if visitas:
                    for v in visitas:
                        with st.expander(f"Fecha: {v['fecha']} - Servicio: {v['servicio']}"):
                            st.write(f"Atendida por: {v['estilista']}")
                            st.info(f"Formula: {v['formula']}")
                            st.write(f"Observaciones: {v['observaciones']}")
                else:
                    st.write("Aun no hay visitas registradas.")
            else:
                st.warning("No se encontro a la clienta.")

    # --- SECCION 2: REGISTRAR VISITA (Deteccion y Actualizacion Inteligente) ---
    elif opcion == "Registrar Visita":
        st.title("Registrar Nueva Visita")
        nombre_input = st.text_input("Nombre de la clienta:")
        
        if nombre_input:
            # Busqueda exacta para determinar si el cliente ya existe
            existe = clientes_col.find_one({"nombre": nombre_input})
            
            with st.form("form_registro", clear_on_submit=True):
                if existe:
                    st.success(f"Reconocida: {nombre_input}. ¿Quieres actualizar su foto?")
                    telefono = existe["telefono"]
                else:
                    st.info("Nueva clienta detectada.")
                    telefono = st.text_input("Telefono:")
                
                foto_up = st.file_uploader("Subir/Actualizar Foto", type=["jpg", "png", "jpeg"])

                col_a, col_b = st.columns(2)
                with col_a:
                    fecha = st.date_input("Fecha", date.today())
                    estilista = st.text_input("Estilista")
                with col_b:
                    serv = st.selectbox("Servicio", ["Corte", "Tinte", "Peinado", "Tratamiento", "B.Color", "Efecto", "Retoque", "C.Global", "Otro"])
                
                formula = st.text_area("Formula")
                obs = st.text_area("Observaciones")
                
                if st.form_submit_button("Guardar Registro"):
                    img_str = imagen_a_base64(foto_up)
                    
                    if existe:
                        id_c = existe["_id"]
                        if img_str:
                            clientes_col.update_one({"_id": id_c}, {"$set": {"foto_perfil": img_str}})
                    else:
                        if nombre_input and telefono:
                            nuevo_cliente = {
                                "nombre": nombre_input,
                                "telefono": telefono,
                                "foto_perfil": img_str
                            }
                            resultado = clientes_col.insert_one(nuevo_cliente)
                            id_c = resultado.inserted_id
                        else:
                            st.error("Datos obligatorios faltantes.")
                            st.stop()
                    
                    # Guardamos la visita usando la referencia del ObjectId de MongoDB
                    nueva_visita = {
                        "id_cliente": id_c,
                        "fecha": str(fecha),
                        "estilista": estilista,
                        "servicio": serv,
                        "formula": formula,
                        "observaciones": obs
                    }
                    visitas_col.insert_one(nueva_visita)
                    st.success("¡Todo guardado correctamente en la nube!")
        else:
            st.write("Escribe el nombre para empezar.")

    # --- SECCION 3: ADMINISTRACION Y RESPALDO (Sin IDs manuales que acomodar) ---
    elif opcion == "Administrar Sistema":
        st.title("Panel de Administracion")
        
        # Obtenemos todos los clientes de la coleccion
        todos_clientes = list(clientes_col.find())
        
        if todos_clientes:
            # Construimos la tabla para visualizacion con Pandas usando los ObjectIds unicos de MongoDB
            tabla_datos = []
            for c in todos_clientes:
                tabla_datos.append({
                    "ID Interno": str(c["_id"]),
                    "Nombre": c["nombre"],
                    "Telefono": c["telefono"]
                })
            
            st.subheader("Lista de Clientas Activas")
            st.dataframe(pd.DataFrame(tabla_datos), use_container_width=True)
            
            # Botones de Respaldo CSV directos desde la nube
            st.markdown("---")
            st.subheader("Respaldos de Seguridad")
            
            df_c_descarga = pd.DataFrame(tabla_datos)
            csv_c = df_c_descarga.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Lista de Clientes (CSV)", csv_c, "clientes_cloud.csv", "text/csv")
            
            todos_visitas = list(visitas_col.find())
            if todos_visitas:
                tabla_visitas = []
                for v in todos_visitas:
                    tabla_visitas.append({
                        "ID Visita": str(v["_id"]),
                        "ID Cliente": str(v["id_cliente"]),
                        "Fecha": v["fecha"],
                        "Servicio": v["servicio"],
                        "Formula": v["formula"],
                        "Observaciones": v["observaciones"]
                    })
                df_v_descarga = pd.DataFrame(tabla_visitas)
                csv_v = df_v_descarga.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar Historial de Visitas (CSV)", csv_v, "historial_cloud.csv", "text/csv")
            
            # Eliminacion limpia: MongoDB se encarga de los identificadores unicos sin desordenar nada
            st.markdown("---")
            st.subheader("Zona de Eliminacion")
            id_borrar_str = st.text_input("Ingresa el 'ID Interno' de la clienta a eliminar:")
            
            if st.button("Eliminar Permanentemente"):
                if id_borrar_str:
                    try:
                        obj_id = ObjectId(id_borrar_str)
                        # Borramos visitas asociadas y luego al cliente
                        visitas_col.delete_many({"id_cliente": obj_id})
                        clientes_col.delete_one({"_id": obj_id})
                        st.success("Expediente e historial eliminados correctamente de la nube.")
                        st.rerun()
                    except Exception:
                        st.error("El ID ingresado no es valido.")
                else:
                    st.warning("Por favor ingresa un ID.")
        else:
            st.write("No hay clientas registradas en el sistema cloud.")