import streamlit as st
from datetime import date
import base64
from PIL import Image
import io
import pandas as pd
from pymongo import MongoClient
from bson.objectid import ObjectId

st.set_page_config(layout="wide", page_title="Control Estética Pro ✂️", page_icon="💇‍♀️")

# 1. 🔌 CONEXIÓN A MONGO DB ATLAS
@st.cache_resource
def obtener_conexion_mongo():
    try:
        mongo_uri = st.secrets["mongo"]["uri"]
        client = MongoClient(mongo_uri)
        db = client["control_estetica"]
        return db
    except Exception as e:
        st.error(f"❌ Error de conexión a MongoDB: {e}")
        return None

db = obtener_conexion_mongo()

# 2. 📸 FUNCIÓN PARA ENCOGER Y CONVERTIR IMAGEN (Estabilidad móvil)
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

# 3. 🔐 SISTEMA DE CONTROL DE ACCESO (MULTICUENTA)
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""

def login():
    st.title("✨ Bienvenida a Control Estética Pro ✨")
    st.subheader("🔑 Inicia sesión para continuar")
    
    with st.form("form_login"):
        usuario_input = st.text_input("👤 Usuario:")
        password_input = st.text_input("🔒 Contraseña:", type="password")
        boton_entrar = st.form_submit_button("🚀 Ingresar al Sistema")
        
        if boton_entrar:
            # Validamos contra los secretos guardados en Streamlit
            if usuario_input in st.secrets["usuarios"] and st.secrets["usuarios"][usuario_input] == password_input:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario_input
                st.success(f"¡Bienvenido de vuelta, {usuario_input}! 👋")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos. Intenta de nuevo.")

def logout():
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.rerun()

# --- VALIDACIÓN DE SESIÓN ---
if not st.session_state["autenticado"]:
    login()
else:
    # 4. 🧭 NAVEGACIÓN Y MENÚ LATERAL
    st.sidebar.title("👑 Menú Principal")
    st.sidebar.write(f"👤 Sesión activa: **{st.session_state['usuario']}**")
    
    opcion = st.sidebar.radio("Ir a:", [
        "🔍 Buscar y Ver Historial", 
        "📝 Registrar Visita", 
        "⚙️ Administrar Sistema"
    ])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        logout()

    if db is None:
        st.error("🛑 No se pudo establecer comunicación con la base de datos en la nube.")
    else:
        clientes_col = db["clientes"]
        visitas_col = db["visitas"]

        # --- 🔍 SECCIÓN 1: BUSCAR SOLO POR NOMBRE ---
        if opcion == "🔍 Buscar y Ver Historial":
            st.title("📂 Expediente Clínico de Clientas")
            nom_b = st.text_input("🔍 Escribe el nombre de la clienta para buscar:")
            
            if nom_b:
                cliente = clientes_col.find_one({"nombre": {"$regex": nom_b, "$options": "i"}})
                
                if cliente:
                    st.markdown("---")
                    col_info, col_foto = st.columns([2, 1])
                    with col_info:
                        st.header(f"👤 Clienta: {cliente['nombre']}")
                        st.subheader(f"📞 Teléfono: {cliente['telefono']}")
                    with col_foto:
                        if "foto_perfil" in cliente and cliente["foto_perfil"]:
                            try:
                                st.image(f"data:image/png;base64,{cliente['foto_perfil']}", width=250)
                            except:
                                st.error("⚠️ Error al mostrar la foto de perfil.")
                        else:
                            st.image("https://via.placeholder.com/250?text=Sin+Foto+📷")

                    st.markdown("---")
                    st.subheader("📜 Historial Cronológico de Visitas")
                    visitas = list(visitas_col.find({"id_cliente": cliente["_id"]}).sort("fecha", 1))
                    
                    if visitas:
                        for v in visitas:
                            with st.expander(f"📅 Fecha: {v['fecha']}  |  💇‍♀️ Servicio: {v['servicio']}"):
                                st.write(f"👤 **Atendida por:** {v['estilista']}")
                                st.info(f"🧪 **Fórmula Aplicada:**\n\n{v['formula']}")
                                st.write(f"📝 **Observaciones:** {v['observaciones']}")
                    else:
                        st.info("ℹ️ Esta clienta aún no tiene visitas registradas.")
                else:
                    st.warning("🕵️‍♂️ No se encontró ninguna clienta con ese nombre.")

        # --- 📝 SECCIÓN 2: REGISTRAR VISITA ---
        elif opcion == "📝 Registrar Visita":
            st.title("📝 Registro de Nueva Visita")
            nombre_input = st.text_input("👤 Nombre completo de la clienta:")
            
            if nombre_input:
                existe = clientes_col.find_one({"nombre": nombre_input})
                
                with st.form("form_registro", clear_on_submit=True):
                    if existe:
                        st.success(f"✨ Clienta reconocida: **{nombre_input}**. ¿Deseas actualizar su foto de perfil?")
                        telefono = existe["telefono"]
                    else:
                        st.info("🆕 ¡Nueva clienta detectada! Llena sus datos de contacto.")
                        telefono = st.text_input("📞 Teléfono:")
                    
                    foto_up = st.file_uploader("📷 Subir o Actualizar Foto de Perfil", type=["jpg", "png", "jpeg"])

                    col_a, col_b = st.columns(2)
                    with col_a:
                        fecha = st.date_input("📅 Fecha del Servicio", date.today())
                        estilista = st.text_input("💇‍♀️ Estilista que atiende:")
                    with col_b:
                        serv = st.selectbox("🎨 Tipo de Servicio", ["Corte", "Tinte", "Peinado", "Tratamiento", "B.Color", "Efecto", "Retoque", "C.Global", "Otro"])
                    
                    formula = st.text_area("🧪 Fórmula Química / Mezcla aplicada:")
                    obs = st.text_area("✍️ Observaciones adicionales (Estado del cabello, detalles, etc.):")
                    
                    if st.form_submit_button("💾 Guardar en Expediente"):
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
                                st.error("🛑 Error: El Nombre y el Teléfono son completamente obligatorios para registrar nuevas fichas.")
                                st.stop()
                        
                        nueva_visita = {
                            "id_cliente": id_c,
                            "fecha": str(fecha),
                            "estilista": estilista,
                            "servicio": serv,
                            "formula": formula,
                            "observaciones": obs
                        }
                        visitas_col.insert_one(nueva_visita)
                        st.success("✅ ¡Visita y datos guardados de forma segura en MongoDB Atlas!")
            else:
                st.write("💡 Escribe el nombre de la clienta arriba para desplegar el formulario.")

        # --- ⚙️ SECCIÓN 3: ADMINISTRACIÓN Y RESPALDO ---
        elif opcion == "⚙️ Administrar Sistema":
            st.title("⚙️ Panel de Control y Administración")
            
            todos_clientes = list(clientes_col.find())
            
            if todos_clientes:
                tabla_datos = []
                for c in todos_clientes:
                    tabla_datos.append({
                        "🔑 ID Interno (Mongo)": str(c["_id"]),
                        "👤 Nombre": c["nombre"],
                        "📞 Teléfono": c["telefono"]
                    })
                
                st.subheader("📋 Directorio de Clientas Activas")
                st.dataframe(pd.DataFrame(tabla_datos), use_container_width=True)
                
                # --- RESPALDOS CLOUD ---
                st.markdown("---")
                st.subheader("📥 Copias de Seguridad (Respaldos)")
                st.write("Descarga bases de datos actualizadas directo a tu dispositivo en formato CSV.")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    df_c_descarga = pd.DataFrame(tabla_datos)
                    csv_c = df_c_descarga.to_csv(index=False).encode('utf-8')
                    st.download_button("👥 Descargar Lista de Clientes (CSV)", csv_c, "clientes_cloud.csv", "text/csv")
                
                with col_btn2:
                    todos_visitas = list(visitas_col.find())
                    if todos_visitas:
                        tabla_visitas = []
                        for v in todos_visitas:
                            tabla_visitas.append({
                                "ID Visita": str(v["_id"]),
                                "ID Cliente": str(v["id_cliente"]),
                                "Fecha": v["fecha"],
                                "Servicio": v["servicio"],
                                "Fórmula": v["formula"],
                                "Observaciones": v["observaciones"]
                            })
                        df_v_descarga = pd.DataFrame(tabla_visitas)
                        csv_v = df_v_descarga.to_csv(index=False).encode('utf-8')
                        st.download_button("📜 Descargar Historial Completo (CSV)", csv_v, "historial_cloud.csv", "text/csv")
                
                # --- ZONA DE ELIMINACIÓN ---
                st.markdown("---")
                st.subheader("🚨 Zona de Peligro (Eliminar Registros)")
                id_borrar_str = st.text_input("💥 Ingresa el 'ID Interno (Mongo)' de la clienta:")
                
                if st.button("🗑️ Eliminar Permanentemente"):
                    if id_borrar_str:
                        try:
                            obj_id = ObjectId(id_borrar_str)
                            # Borramos historial y luego perfil
                            visitas_col.delete_many({"id_cliente": obj_id})
                            clientes_col.delete_one({"_id": obj_id})
                            st.success("💥 Expediente e historial borrados permanentemente de la nube.")
                            st.rerun()
                        except Exception:
                            st.error("❌ El formato del ID ingresado no corresponde a las llaves de MongoDB Atlas.")
                    else:
                        st.warning("⚠️ Por favor escribe un ID válido antes de presionar el botón.")
            else:
                st.info("💼 No hay clientas registradas todavía en este servidor.")