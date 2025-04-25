from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3
import db
import secrets
import csv
from flask import Response
import pandas as pd
import json

""" import logging

# Configurar el logger
logging.basicConfig(level=logging.DEBUG)  # Puedes cambiar el nivel a INFO, WARNING, ERROR, etc. """

app = Flask(__name__)
print(secrets.token_hex(32))  # Genera una clave secreta segura para producción
app.secret_key = secrets.token_hex(32)  # Genera una clave secreta segura para producción


# Inicializar la base de datos
db.init_db()


@app.route('/')
def index():
    # Obtener el valor del parámetro filtro de la URL, (por ejemplo para buscar pacientes por nombre o diagnóstico)
    # si no se proporciona un filtro se usa una cadena vacia con valor predeterminado
    filtro = request.args.get('filtro', '')

    # Obtener el valor del parametro 'pagina' de la URL, que indica la página actual de los resultados
    # Si no se proporciona, se establece en 1 por defecto
    pagina = int(request.args.get('pagina', 1))

    # definir el número de resultados por página
    por_pagina = 7

    # obtener la lista de pacientes de la base de datos
    pacientes, total = db.obtener_pacientes(filtro=filtro, pagina=pagina, por_pagina=por_pagina)

    # calcula el total de páginas necesarias para mosotrar los resultados, redondeando hacia arriba
    total_paginas = (total + por_pagina - 1) // por_pagina

    # Renderiza la plantilla index, pasando los datos necesarios para mostrar la vista
    return render_template('index.html', pacientes=pacientes, 
                           filtro=filtro, 
                           pagina=pagina, 
                           total_paginas=total_paginas)


@app.route('/nuevo_paciente', methods=['GET', 'POST'])
def nuevo_paciente():
    if request.method == 'POST':
        # obtener los datos del formulario
        nombre = request.form['nombre']
        edad = request.form['edad']
        diagnostico = request.form['diagnostico']
        
        if not nombre or not edad or not diagnostico:
            flash('Por favor, completa todos los campos son obligatorios.')
            return redirect(url_for('nuevo_paciente'))

        # agregar el nuevo paciente a la base de datos
        db.agregar_paciente(nombre, edad, diagnostico)
        flash('Paciente agregado exitosamente.')
                
        # redirigir a la página principal
        return redirect(url_for('index'))
      
    # Si la solicitud es GET, simplemente renderizamos el formulario
    return render_template('nuevo_paciente.html')


# Ruta editar un paciente. acepta metodos GET y POST
@app.route('/editar_paciente/<int:id>', methods=['GET', 'POST'])
def editar_paciente(id):
    # obtener el paciente de la base de datos
    paciente = db.obtener_paciente_por_id(id)
    
    # si el formulario fué enviado con el método POST
    if request.method == 'POST':
        # obtener los datos del formulario
        nombre = request.form['nombre']
        edad = request.form['edad']
        diagnostico = request.form['diagnostico']

        # verificar si los campos no están vacios
        if not nombre or not edad or not diagnostico:
            flash('Por favor, completa todos los campos son obligatorios.')
            return redirect(url_for('editar_paciente', id=id))

        # actualizar el paciente en la base de datos
        db.actualizar_paciente(id, nombre, int(edad), diagnostico)
        flash('Paciente actualizado exitosamente.')
        
        # redirigir a la página principal
        return redirect(url_for('index'))
    
    # Si la solicitud es GET, simplemente renderizamos el formulario
    return render_template('editar_paciente.html', paciente=paciente)


# define una ruta que responda a solicitudes POST para eliminar un paciente con un ID específico
@app.route('/eliminar_paciente/<int:id>', methods=['POST'])
def eliminar_paciente(id):
    # llamamos a la función eliminar_paciente de db.py
    db.eliminar_paciente(id)
    flash('Paciente eliminado exitosamente.')
    # redirigir a la página principal
    return redirect(url_for('index'))

#Ruta para el inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    #Verificamos si el método de la solicitud es POST
    if request.method == 'POST':
        # comprobamos si el usuario y la contraseña son correctos usando la función
        # verificar_usuario de db.py
        if db.verificar_usuario(request.form['usuario'], request.form['contraseña']):
            # Si son correctas, almacenamos el nombre de usuario en la sesión
            session['usuario'] = request.form['usuario']


            #Mostramos el mensaje del inicio de sesión exitoso
            flash('Inicio de sesión exitoso.')
            return redirect(url_for('index'))
        else:
            #si no son correctas, mostramos un mensaje de error
            flash('Usuario o contraseña incorrectos.')

    # Si el método de la solicitud es GET(cuando se carga la página del formulario), 
    # renderizamos la plantilla de inicio de sesión
    return render_template('login.html')

# Ruta para manejar el registro de usuarios
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    # verificamos si el metodo de la solicitud es 'POST' (el usuario envió el formulario)
    if request.method == 'POST':
        # Intentamos registrar el usuario usando la función registrar_usuario
        exito = db.registrar_usuario(request.form['usuario'], request.form['contraseña'])
        if exito: 
            #Mostramos el mensaje
            flash("El usuario fue registrado. Ahora puedes iniciar sesión", "success")

            # Redirigimos al usuario a la página de inicio de sesión
            return redirect(url_for('login'))
        else: 
            # Error el usuario ya existe
            flash('Ese usuario ya existe.' 'danger')

    return render_template('register.html')

# Ruta de cerrar sesión 
@app.route('/logout')
def logout():

    #Eliminamos el nombre de usuario de la sesión
    session.pop('usuario', None)
    # Limpiamos la sesión del usuario
    flash('Sesión cerrada exitosamente.')
    # Redirigimos al usuario a la página de inicio
    return redirect(url_for('index'))


# Se usa para que antes de cualquier requierimiento se ejecute "requerir_login()"
@app.before_request
def requerir_login():
    #esta función se asegura de que los usuarios que intenten acceder a ciertas rutas
    #estén autenticados
    rutas_libres = ['login', 'registro', 'static']

    if request.endpoint not in rutas_libres and 'usuario' not in session: 
        return redirect(url_for('login'))
    
    

@app.route('/exportar_csv', methods=['GET'])
def exportar_csv():
    #conectamos a la base de datos
    conn = sqlite3.connect('data.db')
    #creamos un cursor para ejecutar comandos SQL
    cursor = conn.cursor()
    #ejecutamos el comando SQL para obtener todos los pacientes
    cursor.execute('SELECT nombre, edad, diagnostico FROM Pacientes')

    #obtenemos todos los resultados
    filas = cursor.fetchall()
    #obtenemos los nombres de las columnas
    
    conn.close()



    def generar_csv():

        yield 'Nombre,Edad,Diagnostico\n'  # Encabezados del CSV

        for fila in filas:
            yield f'{fila[0]},{fila[1]},{fila[2]}\n'  # Datos de cada paciente
            #para cada linea, generamos una línea CSV con los datos del paciente

    
    return Response(generar_csv(), mimetype='text/csv',
            headers = {'Content-Disposition': 'attachment; filename=pacientes.csv'})

    #Response crea una respuesta http con el contenisdo generado por la funcion generar_csv()
    #'mimetype' especifica el tipo de contenido como csv
    #'headers' especifica el nombre del archivo que se descargará
    #la funcion 'generar_csv()' genera el contendido del archivo CSV linea por linea lo que es eficiente para grandes conjuntos de datos


# Exportar excell
@app.route('/exportar_excel')
def exportar_excel():
    #conectamos a la base de datos
    conn = sqlite3.connect('data.db')

    #pd.read lee los datos de la tabla 'Pacientes' y los almacena en un DataFrame de pandas
    #esto permite manipular y exportar los datos fácilmente
    df = pd.read_sql_query('SELECT nombre, edad, diagnostico FROM Pacientes', conn)
    conn.close()
    
    #creamos un objeto de respuesta Excel
    output = pd.ExcelWriter('pacientes.xlsx', engine='openpyxl')
    df.to_excel(output, index=False, sheet_name='Pacientes')

    output.close()

    #abrimos el archivo Excel en modo lectura binaria('rb') para enviarlo como respuesta
    with open('pacientes.xlsx', 'rb') as f:
       data = f.read()

    #Refresar una respuesta HTTP con el archivo Excel
    return Response(data,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': 'attachment; filename=pacientes.xlsx'})

    # Response crea una respuesta HTTP con el contenido del archivo Excel
    # mimetype especifica el tipo de contenido como Excel    
    # headers especifica el nombre del archivo que se descargará
       

#Funcion para generar las graficas de los pacientes
@app.route('/graficas')
def graficas():
    #consultamos a la base de datos
    conn = sqlite3.connect('data.db')

    #creamos un cursor para ejecutar comandos SQL
    cursor = conn.cursor()
    #ejecutamos el comando SQL para obtener todos los pacientes
    cursor.execute('SELECT diagnostico , COUNT(*) FROM Pacientes GROUP BY diagnostico')
    #obtenemos todos los resultados
    resultados = cursor.fetchall()


    # consulta para obtener distribución de edades de los pacientes
    cursor.execute('SELECT edad FROM Pacientes')
    """filas = cursor.fetchall()
    edades = []
    for fila in filas:
        edades.append(fila[0])"""
    edades = [fila[0] for fila in cursor.fetchall()] #Esto es lo mismo que comentado arriba, pero más compacto
    # cerramos la conexión a la base de datos
    conn.close()

    # Preparamos los datos para las gráficas
    etiquetas = [fila[0] for fila in resultados]
    conteos = [fila[1] for fila in resultados] # número de pacientes por diagnóstico

    return render_template('graficas.html', 
                           etiquetas=json.dumps(etiquetas), 
                           conteos=json.dumps(conteos), 
                           edades=json.dumps(edades))


#app.run(host= '0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    app.run()