import streamlit as st
from datetime import date
import base64
from PIL import Image
import io
import pandas as pd
import hashlib
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configuración única de página combinando tu diseño
st.set_page_config(layout="wide", page_title="Esytetic Manager Pro", page_icon="✂️")

# 1. 🔑 FUNCIÓN ENCRIPTA CONTRASEÑAS (SHA-256)
def encriptar_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 2. 🔌 CONEXIÓN A MONGO DB ATLAS
@st.cache_resource
def obtener_conexion_mongo():
    try:
        mongo_uri = st.secrets["mongo"]["uri"]
        client = MongoClient(mongo_uri)
        db = client["control_estetica_saas"]
        return db
    except Exception as e:
        st.error(f"❌ Error de conexión a MongoDB Atlas: {e}")
        return None

db = obtener_conexion_mongo()

# 3. 📸 FUNCIÓN PARA ENCOGER Y CONVERTIR IMAGEN (Estabilidad móvil)
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

# ==========================================
# 🔐 CONTROL DE SESIONES (SaaS MODEL)
# ==========================================
if 'usuario_id' not in st.session_state:
    st.session_state['usuario_id'] = None
    st.session_state['nombre_negocio'] = None
    st.session_state['usuario_login'] = None
    st.session_state['rol'] = None
    st.session_state['tenant_id'] = None
    st.session_state['logo'] = None
    st.session_state['fondo'] = None

if db is None:
    st.error("🛑 Error crítico: No se pudo conectar con el servidor de la base de datos en la nube.")
    st.stop()

# Inicializamos las colecciones core del ecosistema
usuarios_col = db["usuarios"]
clientes_col = db["clientes"]
visitas_col = db["visitas"]

# ==========================================
# FLUX A: PORTAL DE ACCESO (LOG OUT STATE)
# ==========================================
if st.session_state['usuario_id'] is None:
    st.markdown("""
        <style>
        .stApp { background-color: #0d0d0d; color: #e0e0e0; }
        .stButton>button { background-color: #4b0082; color: white; width: 100%; border-radius: 8px; }
        </style>
        """, unsafe_allow_html=True)

    st.title("🔐 Portal de Administración")
    st.write("Bienvenido al centro de gestión inteligente para salones de belleza y estéticas.")
    
    tab_login, tab_registro = st.tabs(["👤 Iniciar Sesión", "🏢 Registrar Mi Negocio"])
    
    # --- PESTAÑA 1: INICIAR SESIÓN ---
    with tab_login:
        with st.form("form_login"):
            usuario_login = st.text_input("Usuario:").strip().lower()
            pass_login = st.text_input("Contraseña:", type="password")
            
            if st.form_submit_button("Entrar al Sistema"):
                user_db = usuarios_col.find_one({
                    "usuario": usuario_login, 
                    "password": encriptar_pass(pass_login)
                })
                
                if user_db:
                    st.session_state['usuario_id'] = str(user_db["_id"])
                    st.session_state['nombre_negocio'] = user_db["negocio"]
                    st.session_state['usuario_login'] = user_db["usuario"]
                    st.session_state['rol'] = user_db.get("rol", "empleado") # Si no está definido, hereda rol de empleada
                    st.session_state['tenant_id'] = user_db["tenant_id"] # Identificador del local
                    st.session_state['logo'] = user_db.get("logo", None)
                    st.session_state['fondo'] = user_db.get("fondo", "#0d0d0d")
                    st.success("¡Acceso concedido! Cargando panel... 🎉")
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos.")
                        
    # --- PESTAÑA 2: REGISTRAR NUEVO NEGOCIO ---
    with tab_registro:
        st.write("🚀 Crea una infraestructura en la nube exclusiva para tu estética en un minuto.")
        with st.form("form_registro_negocio"):
            nuevo_negocio = st.text_input("Nombre de la Estética / Salón *")
            nuevo_usuario = st.text_input("Crea un Usuario de Administrador (sin espacios) *").strip().lower()
            nueva_pass = st.text_input("Crea una Contraseña Segura *", type="password")
            
            if st.form_submit_button("Agregar Negocio"):
                if usuarios_col.find_one({"usuario": nuevo_usuario}):
                    st.error("❌ Ese nombre de usuario ya está registrado por otra estética. Intenta con otro.")
                elif nuevo_negocio and nuevo_usuario and nueva_pass:
                    nuevo_id = ObjectId()
                    usuarios_col.insert_one({
                        "_id": nuevo_id,
                        "negocio": nuevo_negocio,
                        "usuario": nuevo_usuario,
                        "password": encriptar_pass(nueva_pass),
                        "rol": "administrador", # Cuenta Maestra inicial
                        "tenant_id": str(nuevo_id),
                        "logo": None,
                        "fondo": "#0d0d0d"
                    })
                    st.success("✨ ¡Tu plataforma ha sido inicializada con éxito! Ya puedes iniciar sesión en la primera pestaña.")
                else:
                    st.warning("⚠️ Por favor, llena todos los campos obligatorios marcados con asterisco (*).")

# ==========================================
# FLUX B: SISTEMA OPERATIVO (LOGGED IN STATE)
# ==========================================
else:
    tenant_id = st.session_state['tenant_id']
    rol_usuario = st.session_state['rol']

    # Menú Lateral Personalizado con tu título corporativo
    st.sidebar.title(f"👑 {st.session_state['nombre_negocio']}")
    st.sidebar.write(f"👤 Conectado: **{st.session_state['usuario_login']}** ({rol_usuario.upper()})")
    
    # Restricción de navegación adaptativa: Las empleadas no ven el panel de administración
    opciones_menu = ["🔍 Buscar y Ver Historial", "📝 Registrar Visita"]
    if rol_usuario == "administrador":
        opciones_menu.append("⚙️ Administrar Sistema")
        
    opcion = st.sidebar.radio("Navegación:", opciones_menu)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['usuario_id'] = None
        st.session_state['nombre_negocio'] = None
        st.session_state['usuario_login'] = None
        st.session_state['rol'] = None
        st.session_state['tenant_id'] = None
        st.session_state['logo'] = None
        st.session_state['fondo'] = None
        st.rerun()

    # --- 🔍 SECCIÓN 1: HISTORIAL SEGMENTADO POR NEGOCIO ---
    if opcion == "🔍 Buscar y Ver Historial":
        st.title("📂 Expediente de Clientas")
        nom_b = st.text_input("🔍 Escribe el nombre de la clienta:")
        
        if nom_b:
            cliente = clientes_col.find_one({
                "tenant_id": tenant_id,
                "nombre": {"$regex": nom_b, "$options": "i"}
            })
            
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
                            st.error("⚠️ Error de renderizado en la imagen.")
                    else:
                        st.image("https://via.placeholder.com/250?text=Sin+Foto+📷")

                st.markdown("---")
                st.subheader("📜 Historial de Visitas")
                visitas = list(visitas_col.find({"tenant_id": tenant_id, "id_cliente": cliente["_id"]}).sort("fecha", 1))
                
                if visitas:
                    for v in visitas:
                        with st.expander(f"📅 Fecha: {v['fecha']}  |  💇‍♀️ Servicio: {v['servicio']}"):
                            st.write(f"👤 **Atendida por:** {v['estilista']}")
                            st.info(f"🧪 **Fórmula Aplicada:**\n\n{v['formula']}")
                            st.write(f"📝 **Observaciones:** {v['observaciones']}")
                else:
                    st.info("ℹ️ No hay visitas registradas para esta clienta.")
            else:
                st.warning("🕵️‍♂️ No se encontró ninguna clienta activa con ese nombre en tu negocio.")

    # --- 📝 SECCIÓN 2: REGISTRAR VISITA CON SEGMENTACIÓN ---
    elif opcion == "📝 Registrar Visita":
        st.title("📝 Control de Visita")
        nombre_input = st.text_input("👤 Nombre completo de la clienta:")
        
        if nombre_input:
            existe = clientes_col.find_one({"tenant_id": tenant_id, "nombre": nombre_input})
            
            with st.form("form_registro", clear_on_submit=True):
                if existe:
                    st.success(f"✨ Clienta existente. ¿Deseas refrescar su foto de perfil?")
                    telefono = existe["telefono"]
                else:
                    st.info("🆕 ¡Nueva clienta detectada en tu base de datos! Completa los campos:")
                    telefono = st.text_input("📞 Teléfono:")
                
                foto_up = st.file_uploader("📷 Foto de Expediente", type=["jpg", "png", "jpeg"])

                col_a, col_b = st.columns(2)
                with col_a:
                    fecha = st.date_input("📅 Fecha", date.today())
                    # Si es empleada se bloquea el input y se inyecta su propio usuario de forma transparente
                    if rol_usuario == "empleado":
                        estilista = st.text_input("💇‍♀️ Estilista:", value=st.session_state['usuario_login'], disabled=True)
                    else:
                        estilista = st.text_input("💇‍♀️ Estilista:", value=st.session_state['usuario_login'])
                with col_b:
                    serv = st.selectbox("🎨 Servicio Realizado", ["Corte", "Tinte", "Peinado", "Tratamiento", "B.Color", "Efecto", "Retoque", "C.Global", "Otro"])
                
                formula = st.text_area("🧪 Fórmula / Mezcla Química:")
                obs = st.text_area("✍️ Notas de Seguimiento:")
                
                if st.form_submit_button("💾 Guardar Datos"):
                    img_str = imagen_a_base64(foto_up)
                    
                    if existe:
                        id_c = existe["_id"]
                        if img_str:
                            clientes_col.update_one({"_id": id_c}, {"$set": {"foto_perfil": img_str}})
                    else:
                        if nombre_input and telefono:
                            nuevo_cliente = {
                                "tenant_id": tenant_id,
                                "nombre": nombre_input,
                                "telefono": telefono,
                                "foto_perfil": img_str
                            }
                            resultado = clientes_col.insert_one(nuevo_cliente)
                            id_c = resultado.inserted_id
                        else:
                            st.error("🛑 El nombre y teléfono son requeridos para altas de clientes.")
                            st.stop()
                    
                    nueva_visita = {
                        "tenant_id": tenant_id,
                        "id_cliente": id_c,
                        "fecha": str(fecha),
                        "estilista": estilista,
                        "servicio": serv,
                        "formula": formula,
                        "observaciones": obs
                    }
                    visitas_col.insert_one(nueva_visita)
                    st.success("✅ ¡Servicio guardado en la nube de tu sucursal de forma exitosa!")
        else:
            st.write("💡 Ingresa el nombre de la clienta para cargar la interfaz de registro.")

    # --- ⚙️ SECCIÓN 3: ADMINISTRACIÓN SEGURA (TENANT LEVEL CON GESTIÓN DE EMPLEADAS ILIMITADAS N) ---
    elif opcion == "⚙️ Administrar Sistema" and rol_usuario == "administrador":
        st.title("⚙️ Consola de Administración Privada")
        st.write(f"Espacio corporativo de: **{st.session_state['nombre_negocio']}**")
        
        tab_usuarios, tab_datos, tab_eliminar = st.tabs(["👥 Control de Empleadas", "📥 Copias de Respaldo", "🚨 Zona de Baja"])
        
        # --- SUB-TAB 1: CONTROL DE EMPLEADAS (REGISTRO N) ---
        with tab_usuarios:
            st.subheader("🏗️ Registrar Nueva Trabajadora / Estilista")
            st.write("Crea accesos individuales ilimitados para tu personal vinculados a tu tenant.")
            
            with st.form("form_alta_empleado", clear_on_submit=True):
                nom_usuario_emp = st.text_input("Crea el Usuario de la empleada (sin espacios):").strip().lower()
                pass_usuario_emp = st.text_input("Crea su Contraseña Temporal:", type="password")
                
                if st.form_submit_button("➕ Registrar Cuenta de Empleada"):
                    if usuarios_col.find_one({"usuario": nom_usuario_emp}):
                        st.error("❌ Este nombre de usuario ya existe en el sistema global. Elige otro.")
                    elif nom_usuario_emp and pass_usuario_emp:
                        usuarios_col.insert_one({
                            "negocio": st.session_state['nombre_negocio'],
                            "usuario": nom_usuario_emp,
                            "password": encriptar_pass(pass_usuario_emp),
                            "rol": "empleado", 
                            "tenant_id": tenant_id # Se amarra en automático al negocio del administrador
                        })
                        st.success(f"✅ ¡Cuenta de empleada para '**{nom_usuario_emp}**' creada exitosamente!")
                    else:
                        st.warning("⚠️ Completa los campos del formulario.")
            
            st.markdown("---")
            st.subheader("👥 Plantilla de Empleados en tu Sucursal")
            lista_empleados = list(usuarios_col.find({"tenant_id": tenant_id}))
            if lista_empleados:
                tabla_emp = []
                for emp in lista_empleados:
                    tabla_emp.append({
                        "Usuario": emp["usuario"],
                        "Rango de Acceso": emp.get("rol", "empleado").upper()
                    })
                st.table(pd.DataFrame(tabla_emp))

        # --- SUB-TAB 2: RESPALDOS CLOUD ---
        with tab_datos:
            mis_clientes = list(clientes_col.find({"tenant_id": tenant_id}))
            
            if mis_clientes:
                tabla_datos = []
                for c in mis_clientes:
                    tabla_datos.append({
                        "🔑 Clave Interna": str(c["_id"]),
                        "👤 Clienta": c["nombre"],
                        "📞 Teléfono": c["telefono"]
                    })
                
                st.subheader("📋 Tu Catálogo de Clientes Activos")
                st.dataframe(pd.DataFrame(tabla_datos), use_container_width=True)
                
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    df_c_descarga = pd.DataFrame(tabla_datos)
                    csv_c = df_c_descarga.to_csv(index=False).encode('utf-8')
                    st.download_button("👥 Exportar Base de Clientes (CSV)", csv_c, "mis_clientes.csv", "text/csv")
                
                with col_btn2:
                    mis_visitas = list(visitas_col.find({"tenant_id": tenant_id}))
                    if mis_visitas:
                        tabla_visitas = []
                        for v in mis_visitas:
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
                        st.download_button("📜 Exportar Registro de Visitas (CSV)", csv_v, "mi_historial.csv", "text/csv")
            else:
                st.info("💼 No tienes clientas dadas de alta en tu base de datos todavía.")

        # --- SUB-TAB 3: ZONA DE ELIMINACIÓN ---
        with tab_eliminar:
            st.subheader("🚨 Remover Registro del Servidor")
            id_borrar_str = st.text_input("💥 Clave Interna de la clienta a dar de baja:")
            
            if st.button("🗑️ Confirmar Baja Permanente"):
                if id_borrar_str:
                    try:
                        obj_id = ObjectId(id_borrar_str)
                        control_verificacion = clientes_col.find_one({"_id": obj_id, "tenant_id": tenant_id})
                        
                        if control_verificacion:
                            visitas_col.delete_many({"id_cliente": obj_id, "tenant_id": tenant_id})
                            clientes_col.delete_one({"_id": obj_id, "tenant_id": tenant_id})
                            st.success("💥 Expediente y citas eliminados de la red de tu negocio.")
                            st.rerun()
                        else:
                            st.error("🛑 Permiso Denegado: No puedes alterar expedientes de otras estéticas.")
                    except Exception:
                        st.error("❌ La clave ingresada no pertenece al formato nativo del clúster.")
                else:
                    st.warning("⚠️ Por favor introduce una clave válida para proceder.")