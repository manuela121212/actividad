import streamlit as st
import pandas as pd
import datetime
import sqlite3
import re

st.set_page_config(page_title='FORMULARIO')
st.title('Actividad formularios')

# crear la BBDD y la tabla
def inicializar_db():
    conexion = sqlite3.connect('uni.db')
    cursor = conexion.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ESTUDIANTES
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                correo TEXT,
                password TEXT
            )
    ''')
    conexion.commit()
    conexion.close()

def inicializar_historial():
    conexion = sqlite3.connect('uni.db')
    cursor = conexion.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS HISTORIAL
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
                accion TEXT,
                fecha_hora TEXT
            )
    ''')
    conexion.commit()
    conexion.close()

# CARGAR CSS DESDE UN ARCHIVO EXTERNO
def cargar_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

cargar_css('styles.css')

# función para insertar un nuevo registro
def registrar_estudiante(nombre, correo, password):
    conexion = sqlite3.connect('uni.db')
    cursor = conexion.cursor()

    # verificar si ya existe un estudiante con esos datos
    cursor.execute("SELECT id FROM ESTUDIANTES WHERE nombre = ? OR correo = ? ", (nombre, correo))
    if cursor.fetchone():
        conexion.close()
        return False # significa que ya existe 

    # insertar nuevo estudiante
    cursor.execute("INSERT INTO ESTUDIANTES (nombre, correo, password) VALUES (?,?,?)", (nombre, correo, password))
    conexion.commit()
    conexion.close()
    return True

#función para contraseña segura
def verificar_requisitos(password):
    requisitos = {
        "Al menos 8 caracteres" : len(password)>=8,
        "Al menos una letra minúscula" : bool(re.search(r"[a-z]", password)),
        "Al menos una letra mayúscula" : bool(re.search(r"[A-Z]", password)),
        "Al menos un número" : bool(re.search(r"[0-9]", password)),
        "Al menos un caracter especial" : bool(re.search(r"[!@#$%^&*(),]", password))  
    }
    return requisitos

#función para verificar si ya existe el estudiante
def verificar_estudiante(nombre, password):
    conexion = sqlite3.connect('uni.db')
    cursor = conexion.cursor()

    cursor.execute("SELECT id, password FROM ESTUDIANTES WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    conexion.close()

    if resultado:
        return resultado[1] == password #¿La contraseña que está guardada es igual a la que escribió el usuario?
    else:
        return None
    
# función para el historial
def registrar_accion(usuario, accion):
    conexion = sqlite3.connect('uni.db')
    cursor = conexion.cursor()

    fecha = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    cursor.execute('INSERT INTO HISTORIAL (usuario, accion, fecha_hora) VALUES (?,?,?)',(usuario, accion, fecha))

    conexion.commit()
    conexion.close()

#inicializar BBDD
inicializar_db()

# inicializar historial
inicializar_historial()

#menú lateral
menu = ['Inicio', 'Formulario de ingreso - Registro', 'BBDD', 'Historial']
seleccion = st.sidebar.selectbox('Selecciona una opción', menu)

if seleccion == 'Inicio':
    st.header('BIENVENIDO')
    st.write('''
        Aquí encontrarás:
        - Inicio de sesión para ingresar a la base de datos de la universidad
        - Registro de usuario y contraseña para estudiantes
        - Visualización y descarga de BBDD
        - Historial de acciones en los formularios
    ''')

elif seleccion == 'Formulario de ingreso - Registro':
    st.title('Inicio de sesión')

    if 'mostrar_registro' not in st.session_state:
        st.session_state.mostrar_registro = False

    # login
    if not st.session_state.mostrar_registro:
        with st.form(key='login_form'):
            usuario_login = st.text_input('Nombre de usuario')
            correo_login = st.text_input('Correo')
            password_login = st.text_input('Contraseña', type='password')
            enviar_login = st.form_submit_button(label='Iniciar sesión')

        if enviar_login:
            if usuario_login.strip() == '' or correo_login.strip() == '' or password_login.strip() == '':
                st.warning('Por favor completa todos los campos')
                registrar_accion(usuario_login, accion='Intento de sesión con campos vacíos')
            else:
                validacion = verificar_estudiante(usuario_login, password_login)

                if validacion is None:
                    st.error('Usuario no registrado')
                    registrar_accion(usuario_login, accion='Intento de sesión con usuario no registrado')
                elif validacion:
                    st.success(f'Bienvenid@ {usuario_login}')
                    registrar_accion(usuario_login, accion='Sesión iniciada con éxito')
                else:
                    st.error('Usuario o contraseña incorrecta')
                    registrar_accion(usuario_login, accion='Intento de sesión con usuario o contraseña incorrecta')
        
        if st.button('¿No tienes cuenta? Regístrate'):
            st.session_state.mostrar_registro = True
            st.rerun()

    # registro
    else:
        st.subheader('Formulario de registro')

        with st.form(key='registro_form'):
            usuario_registro = st.text_input('Elige un nombre de usuario')
            correo_registro = st.text_input('Escribe tu dirección de correo')
            password_registro = st.text_input('Elige una contraseña', type='password')

            if password_registro:
                st.markdown('### Requisitos de la contraseña: ')
                requisitos = verificar_requisitos(password_registro)

                for k,v in requisitos.items():
                    if v:
                        st.markdown(f'✔️{k}')
                    else:
                        st.markdown(f'✖️{k}')

            enviar_registro = st.form_submit_button(label='Registrarse')

        if enviar_registro:
            if usuario_registro.strip() == '' or correo_registro.strip() == '' or password_registro.strip() == '':
                st.warning('Por favor completa todos los campos')

            elif not all(verificar_requisitos(password_registro).values()):
                st.error('Requisitos no cumplidos')

            elif registrar_estudiante(usuario_registro, correo_registro, password_registro):
                st.success(f'Usuario {usuario_registro} creado con éxito')
                st.session_state.mostrar_registro = False

            else:
                st.error('El usuario ya existe en la BBDD')
        
        if st.button('¿Ya tienes cuenta? Inicia sesión'):
            st.session_state.mostrar_registro = False

elif seleccion == 'BBDD':
    st.markdown('---')
    st.header('Acceso a base de datos')

    # contraseña para ver la base de datos
    clave_correcta = "admin123"

    constrasena_visualizar = st.text_input('Ingresa la contraseña para ver la base de datos', type='password')
    archivo_db = st.file_uploader('Sube el archivo .db de sqlite3', type=['db'])

    if archivo_db and constrasena_visualizar:
        if constrasena_visualizar == clave_correcta:
            
            # guardar el archivo subido
            ruta_temporal = 'subida_temp.db'
            with open(ruta_temporal, 'wb') as f:
                f.write(archivo_db.read())
            
            # conectarse y mostrar las tablas
            conn = sqlite3.connect(ruta_temporal)
            cursor = conn.cursor()

            # obtener las tablas
            cursor.execute('SELECT name FROM sqlite_master WHERE type = "table"')
            tablas = cursor.fetchall()

            if tablas:
                st.success('✔️ Acceso concedido. Mostrando tablas:')
                for nombre_tabla in tablas:
                    nombre = nombre_tabla[0] # me dice que me muestre la primer tabla guardada en sql
                    st.subheader(f'Tabla: {nombre}')
                    df = pd.read_sql(f'SELECT * FROM {nombre}', conn)
                    st.dataframe(df)
            else:
                st.info('La base de datos no contiene tablas')
            conn.close()
        else:
            st.error('Contraseña incorrecta. Acceso denegado')

elif seleccion == 'Historial':
    st.header('Acciones que han realizado los usuarios')

    conexion = sqlite3.connect('uni.db')
    df_historial = pd.read_sql_query('SELECT * FROM HISTORIAL ORDER BY fecha_hora DESC', conexion)
    conexion.close()

    if not df_historial.empty:
        st.dataframe(df_historial)
    else:
        st.info('No hay acciones registradas aún')


