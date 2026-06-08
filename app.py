import streamlit as st
from datetime import date, datetime
import base64
from PIL import Image
import io
import pandas as pd
import hashlib
from pymongo import MongoClient
from bson.objectid import ObjectId
import pytz  # 🕒 LIBRERÍA DE SEGURIDAD PARA RELOJES SATELLITALES CLOUD

# Configuración única de página combinando tu diseño definitivo
st.set_page_config(layout="wide", page_title="Aesthetic Manager Pro", page_icon="✂️")

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
    st.session_state['plan'] = None  
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
                    rol = user_db.get("rol", "empleado")
                    tenant_id_actual = user_db["tenant_id"]
                    
                    admin_negocio = usuarios_col.find_one({"_id": ObjectId(tenant_id_actual), "rol": "administrador"})
                    plan_negocio = admin_negocio.get("plan", "lite") if admin_negocio else "lite"
                    
                    # 🕒 VALIDACIÓN DE HORARIO: Con corrección de Zona Horaria de México
                    if rol == "empleado" and plan_negocio in ["pro", "enterprise"]:
                        if admin_negocio:
                            try:
                                h_apertura_str = admin_negocio.get("hora_apertura", "09:00")
                                h_cierre_str = admin_negocio.get("hora_cierre", "20:00")
                                
                                hora_apertura = datetime.strptime(h_apertura_str, "%H:%M").time()
                                hora_cierre = datetime.strptime(h_cierre_str, "%H:%M").time()
                                
                                # 🔥 SOLUCIÓN CRÍTICA: Forzamos la hora local de México en lugar de UTC del servidor cloud
                                zona_mx = pytz.timezone("America/Mexico_City")
                                hora_actual = datetime.now(zona_mx).time()
                                
                                if not (hora_apertura <= hora_actual <= hora_cierre):
                                    st.error(f"🛑 Acceso Denegado: El horario de acceso para empleadas en este salón es de {h_apertura_str} a {h_cierre_str}. Fuera de este horario el sistema permanece cerrado por seguridad.")
                                    st.stop()
                            except Exception as time_err:
                                st.error(f"⚠️ Error al verificar el formato de horario del salón: {time_err}.")
                                st.stop()
                    
                    st.session_state['usuario_id'] = str(user_db["_id"])
                    st.session_state['nombre_negocio'] = user_db["negocio"]
                    st.session_state['usuario_login'] = user_db["usuario"]
                    st.session_state['rol'] = rol
                    st.session_state['tenant_id'] = tenant_id_actual
                    st.session_state['plan'] = plan_negocio  
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
            
            st.markdown("📦 **Selección del Plan de Negocio:**")
            plan_seleccionado = st.selectbox("Elige el nivel del sistema:", ["lite", "pro", "enterprise"])
            
            st.markdown("🕒 **Configuración de Horarios Laborales (Aplica solo para Pro/Enterprise):**")
            h_apertura = st.text_input("Hora de Apertura (Formato 24h)", value="09:00")
            h_cierre = st.text_input("Hora de Cierre (Formato 24h)", value="20:00")
            
            if st.form_submit_button("Agregar Negocio"):
                if usuarios_col.find_one({"usuario": nuevo_usuario}):
                    st.error("❌ Ese nombre de usuario ya está registrado por otra estética. Intenta con otro.")
                elif nuevo_negocio and nuevo_usuario and nueva_pass:
                    try:
                        datetime.strptime(h_apertura, "%H:%M")
                        datetime.strptime(h_cierre, "%H:%M")
                    except ValueError:
                        st.error("❌ Formato de hora inválido. Usa el formato de 24 horas (ej: 09:30).")
                        st.stop()

                    nuevo_id = ObjectId()
                    usuarios_col.insert_one({
                        "_id": nuevo_id,
                        "negocio": nuevo_negocio,
                        "usuario": nuevo_usuario,
                        "password": encriptar_pass(nueva_pass),
                        "rol": "administrador",
                        "tenant_id": str(nuevo_id),
                        "plan": plan_seleccionado,  
                        "hora_apertura": h_apertura,
                        "hora_cierre": h_cierre,
                        "logo": None,
                        "fondo": "#0d0d0d"
                    })
                    st.success(f"✨ ¡Salón inicializado en Plan {plan_seleccionado.upper()} con éxito! Ya puedes iniciar sesión.")
                else:
                    st.warning("⚠️ Por favor, llena todos los campos obligatorios marcados con asterisco (*).")

# ==========================================
# FLUX B: SISTEMA OPERATIVO (LOGGED IN STATE)
# ==========================================
else:
    tenant_id = st.session_state['tenant_id']
    rol_usuario = st.session_state['rol']
    plan_actual = st.session_state['plan']

    # Menú Lateral Personalizado
    st.sidebar.title(f"👑 {st.session_state['nombre_negocio']}")
    st.sidebar.write(f"👤 Usuario: **{st.session_state['usuario_login']}**")
    st.sidebar.write(f"📦 Plan Activo: **{plan_actual.upper()}**")
    
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
        st.session_state['plan'] = None
        st.session_state['logo'] = None
        st.session_state['fondo'] = None
        st.rerun()

    # --- 🔍 SECCIÓN 1: HISTORIAL SEGMENTADO ---
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

    # --- 📝 SECCIÓN 2: REGISTRAR VISITA ---
    elif opcion == "📝 Registrar Visita":
        st.title("📝 Control de Visita")
        nombre_buscar = st.text_input("👤 Nombre completo de la clienta:").strip()
        
        if nombre_buscar:
            existe = clientes_col.find_one({"tenant_id": tenant_id, "nombre": {"$regex": f"^{nombre_buscar}$", "$options": "i"}})
            
            with st.form("form_registro", clear_on_submit=True):
                if existe:
                    if rol_usuario == "empleado" and plan_actual in ["pro", "enterprise"]:
                        st.warning("🔒 Los datos generales están bloqueados en este plan corporativo. Solo el Admin puede editarlos.")
                        nombre_final = st.text_input("Nombre de la Clienta:", value=existe["nombre"], disabled=True)
                        telefono = st.text_input("📞 Teléfono:", value=existe["telefono"], disabled=True)
                    else:
                        st.success("✨ Modo de edición habilitado.")
                        nombre_final = st.text_input("Nombre de la Clienta:", value=existe["nombre"])
                        telefono = st.text_input("📞 Teléfono:", value=existe["telefono"])
                else:
                    st.info("🆕 ¡Nueva clienta detectada!")
                    nombre_final = st.text_input("Nombre de la Clienta:", value=nombre_buscar)
                    telefono = st.text_input("📞 Teléfono:")
                
                foto_up = st.file_uploader("📷 Foto de Expediente", type=["jpg", "png", "jpeg"])

                col_a, col_b = st.columns(2)
                with col_a:
                    fecha = st.date_input("📅 Fecha", date.today())
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
                        if rol_usuario == "empleado" and plan_actual in ["pro", "enterprise"]:
                            if img_str:
                                clientes_col.update_one({"_id": id_c}, {"$set": {"foto_perfil": img_str}})
                        else:
                            actualizacion = {"nombre": nombre_final, "telefono": telefono}
                            if img_str:
                                actualizacion["foto_perfil"] = img_str
                            clientes_col.update_one({"_id": id_c}, {"$set": actualizacion})
                    else:
                        if nombre_final and telefono:
                            nuevo_cliente = {
                                "tenant_id": tenant_id,
                                "nombre": nombre_final,
                                "telefono": telefono,
                                "foto_perfil": img_str
                            }
                            resultado = clientes_col.insert_one(nuevo_cliente)
                            id_c = resultado.inserted_id
                        else:
                            st.error("🛑 El nombre y teléfono son obligatorios.")
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
                    st.success("✅ Registro guardado correctamente.")
        else:
            st.write("💡 Ingresa el nombre de la clienta.")

    # --- ⚙️ SECCIÓN 3: ADMINISTRACIÓN SEGURA ---
    elif opcion == "⚙️ Administrar Sistema" and rol_usuario == "administrador":
        st.title("⚙️ Consola de Administración Privada")
        st.write(f"Espacio corporativo de: **{st.session_state['nombre_negocio']}** | Plan: **{plan_actual.upper()}**")
        
        tab_usuarios, tab_datos, tab_eliminar = st.tabs(["👥 Control de Empleadas", "📥 Catálogo y Respaldos", "🚨 Zona de Baja"])
        
        # --- SUB-TAB 1: GESTIÓN DE EMPLEADAS ---
        with tab_usuarios:
            st.subheader("🏗️ Registrar o Actualizar Contraseña de Trabajadora")
            
            with st.form("form_alta_empleado", clear_on_submit=True):
                nom_usuario_emp = st.text_input("Usuario de la empleada:").strip().lower()
                pass_usuario_emp = st.text_input("Contraseña:", type="password")
                
                if st.form_submit_button("💾 Guardar / Actualizar Cuenta"):
                    if nom_usuario_emp and pass_usuario_emp:
                        usuario_existente = usuarios_col.find_one({"usuario": nom_usuario_emp})
                        
                        if usuario_existente:
                            if usuario_existente["tenant_id"] == tenant_id:
                                usuarios_col.update_one(
                                    {"_id": usuario_existente["_id"]},
                                    {"$set": {"password": encriptar_pass(pass_usuario_emp)}}
                                )
                                st.success("🔄 Contraseña restablecida.")
                            else:
                                st.error("❌ Este usuario pertenece a otra sucursal.")
                        else:
                            num_empleadas = usuarios_col.count_documents({"tenant_id": tenant_id, "rol": "empleado"})
                            
                            if plan_actual == "lite" and num_empleadas >= 2:
                                st.error("🛑 Límite de Plan alcanzado: Tu plan Lite solo te permite registrar un máximo de 2 empleadas activas.")
                            else:
                                usuarios_col.insert_one({
                                    "negocio": st.session_state['nombre_negocio'],
                                    "usuario": nom_usuario_emp,
                                    "password": encriptar_pass(pass_usuario_emp),
                                    "rol": "empleado", 
                                    "tenant_id": tenant_id
                                })
                                st.success("✅ Cuenta de empleada creada con éxito.")
                                st.rerun()
                    else:
                        st.warning("⚠️ Completa ambos campos.")
            
            st.markdown("---")
            st.subheader("👥 Plantilla de Empleados")
            lista_empleados = list(usuarios_col.find({"tenant_id": tenant_id}))
            if lista_empleados:
                tabla_emp = []
                for emp in lista_empleados:
                    if emp.get("rol") != "administrador":
                        tabla_emp.append({
                            "👤 Usuario": emp["usuario"],
                            "🛡️ Rango de Acceso": emp.get("rol", "empleado").upper()
                        })
                
                if tabla_emp:
                    df_emp = pd.DataFrame(tabla_emp)
                    df_emp.index = df_emp.index + 1
                    st.table(df_emp)
                    
                    with st.form("form_baja_empleado", clear_on_submit=True):
                        usuario_eliminar = st.text_input("👤 Usuario a eliminar:").strip().lower()
                        if st.form_submit_button("🗑️ Eliminar Trabajadora del Sistema"):
                            if usuario_eliminar:
                                emp_verificar = usuarios_col.find_one({"usuario": usuario_eliminar, "tenant_id": tenant_id})
                                if emp_verificar and emp_verificar.get("rol") != "administrador":
                                    usuarios_col.delete_one({"_id": emp_verificar["_id"]})
                                    st.success("💥 Acceso revocado.")
                                    st.rerun()
                                else:
                                    st.error("❌ No se puede eliminar.")
                else:
                    st.info("ℹ️ Tu plantilla no cuenta con empleadas registradas actualmente.")
            else:
                st.info("ℹ️ No hay personal registrado.")

        # --- SUB-TAB 2: CATÁLOGO CON FILTRO DE BÚSQUEDA ---
        with tab_datos:
            st.subheader("📋 Tu Catálogo de Clientes Activos")
            
            filtro_nombre = st.text_input("🔍 Buscar cliente por nombre en el catálogo (Filtro rápido):").strip()
            
            query_clientes = {"tenant_id": tenant_id}
            if filtro_nombre:
                query_clientes["nombre"] = {"$regex": filtro_nombre, "$options": "i"}
                
            mis_clientes = list(clientes_col.find(query_clientes))
            
            if mis_clientes:
                tabla_datos = []
                for c in mis_clientes:
                    tabla_datos.append({
                        "🔑 Clave Interna": str(c["_id"]),
                        "👤 Clienta": c["nombre"],
                        "📞 Teléfono": c["telefono"]
                    })
                
                df_clientes = pd.DataFrame(tabla_datos)
                df_clientes.index = df_clientes.index + 1
                
                st.dataframe(df_clientes, use_container_width=True)
                
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    csv_c = df_clientes.to_csv(index=False).encode('utf-8')
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
                        df_v_descarga.index = df_v_descarga.index + 1 
                        csv_v = df_v_descarga.to_csv(index=False).encode('utf-8')
                        st.download_button("📜 Exportar Registro de Visitas (CSV)", csv_v, "mi_historial.csv", "text/csv")
            else:
                st.info("💼 No se encontraron clientas con ese criterio de búsqueda.")

        # --- SUB-TAB 3: ZONA DE BAJA INTELIGENTE ---
        with tab_eliminar:
            st.subheader("🚨 Remover Registro del Servidor")
            st.write("Busca el nombre de la clienta para cargar su clave interna y procesar la baja de forma segura.")
            
            nombre_baja_buscar = st.text_input("💥 Escribe el nombre de la clienta a dar de baja:").strip()
            
            if nombre_baja_buscar:
                coincidencias = list(clientes_col.find({
                    "tenant_id": tenant_id,
                    "nombre": {"$regex": nombre_baja_buscar, "$options": "i"}
                }))
                
                if coincidencias:
                    opciones_clientes = {f"{c['nombre']} (Tel: {c['telefono']})": c for c in coincidencias}
                    seleccion = st.selectbox("🎯 Selecciona la ficha exacta a eliminar:", list(opciones_clientes.keys()))
                    
                    cliente_a_borrar = opciones_clientes[seleccion]
                    st.error(f"⚠️ ATENCIÓN: Estás a punto de borrar permanentemente el expediente de **{cliente_a_borrar['nombre']}** junto con todo su historial químico.")
                    
                    if st.button("🗑️ Confirmar Baja Permanente del Servidor"):
                        obj_id = cliente_a_borrar["_id"]
                        
                        visitas_col.delete_many({"id_cliente": obj_id, "tenant_id": tenant_id})
                        clientes_col.delete_one({"_id": obj_id, "tenant_id": tenant_id})
                        
                        st.success(f"💥 ¡El expediente de **{cliente_a_borrar['nombre']}** ha sido removido del clúster exitosamente!")
                        st.rerun()
                else:
                    st.warning("🕵️‍♂️ No se encontraron clientas que coincidan con ese nombre en tu local.")
            else:
                st.info("💡 Introduce el nombre de la clienta en el cuadro de arriba para activar los controles de baja.")