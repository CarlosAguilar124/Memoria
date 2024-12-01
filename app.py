from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta'  # Cambia esto por algo seguro en producción

DATABASE = 'usuarios.db'
DATABASE_CONTACTOS = 'contactos.db'
DATABASE_VENTAS = 'ventas.db'

# Crear las bases de datos y tablas si no existen
def crear_base_datos():
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    if not os.path.exists(DATABASE_CONTACTOS):
        with sqlite3.connect(DATABASE_CONTACTOS) as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                CREATE TABLE contactos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    correo TEXT,
                    mensaje TEXT
                )
            ''')
            conn.commit()

    if not os.path.exists(DATABASE_VENTAS):
        with sqlite3.connect(DATABASE_VENTAS) as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio REAL NOT NULL
                )
            ''')
            conn.commit()

crear_base_datos()

# Funciones para obtener conexión a las bases de datos
def obtener_conexion():
    return sqlite3.connect(DATABASE)

def obtener_conexion_contactos():
    return sqlite3.connect(DATABASE_CONTACTOS)

def obtener_conexion_ventas():
    return sqlite3.connect(DATABASE_VENTAS)

# Ruta para la página de inicio de sesión
@app.route('/', methods=['GET', 'POST'])
@app.route('/inicio', methods=['GET', 'POST'])
def inicio():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')
        if not usuario or not contraseña:
            flash("Por favor, completa todos los campos.", "error")
            return redirect(url_for('inicio'))
        
        # Verificación para el administrador
        if usuario == 'admi' and contraseña == '123':
            session['usuario'] = usuario
            return redirect(url_for('admin'))

        # Verificación para usuarios normales
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?', (usuario, contraseña))
            user = cursor.fetchone()
            if user:
                session['usuario'] = usuario
                return redirect(url_for('bienvenida'))
            else:
                flash("Usuario o contraseña incorrectos.", "error")
                return redirect(url_for('inicio'))
    return render_template('inicio.html')

# Ruta para la página de registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if not username or not email or not password:
            flash("Por favor, completa todos los campos.", "error")
            return redirect(url_for('registro'))
        try:
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO usuarios (username, email, password) VALUES (?, ?, ?)', 
                               (username, email, password))
                conn.commit()
            flash("Usuario registrado con éxito.", "success")
            return redirect(url_for('inicio'))
        except sqlite3.IntegrityError:
            flash("El nombre de usuario ya está registrado. Intenta con otro.", "error")
            return redirect(url_for('registro'))
    return render_template('registro.html')

# Ruta para la página de bienvenida
@app.route('/bienvenida', methods=['GET'])
def bienvenida():
    if 'usuario' not in session:
        flash("Por favor, inicia sesión primero.", "error")
        return redirect(url_for('inicio'))
    usuario = session['usuario']
    return render_template('bievenida.html', usuario=usuario)
    
# Ruta para la página del administrador
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'usuario' not in session or session['usuario'] != 'admi':
        flash("Acceso no autorizado.", "error")
        return redirect(url_for('inicio'))

    # Conexión a la base de datos de ventas
    if request.method == 'POST':
        producto = request.form['producto']
        descripcion = request.form['descripcion']
        cantidad = int(request.form['cantidad'])
        precio = float(request.form['precio'])

        # Agregar nueva venta
        with sqlite3.connect(DATABASE_VENTAS) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ventas (producto, descripcion, cantidad, precio) 
                VALUES (?, ?, ?, ?)
            ''', (producto, descripcion, cantidad, precio))
            conn.commit()
        flash("Venta agregada con éxito.", "success")
        return redirect(url_for('admin'))

    # Obtener todas las ventas para mostrarlas
    with sqlite3.connect(DATABASE_VENTAS) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ventas')
        ventas = cursor.fetchall()

    return render_template('index.html', ventas=ventas)

# Ruta para agregar una venta (API)
@app.route('/agregar-venta', methods=['POST'])
def agregar_venta():
    producto = request.form['producto']
    descripcion = request.form['descripcion']
    cantidad = int(request.form['cantidad'])
    precio = float(request.form['precio'])

    # Guardamos los datos en la base de datos
    conn = sqlite3.connect(DATABASE_VENTAS)
    cursor = conn.cursor()
    cursor.execute(''' 
        INSERT INTO ventas (producto, descripcion, cantidad, precio)
        VALUES (?, ?, ?, ?)
    ''', (producto, descripcion, cantidad, precio))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Venta agregada correctamente"})

# Ruta para eliminar una venta
@app.route('/eliminar-venta', methods=['POST'])
def eliminar_venta():
    venta_id = request.json['id']
    
    conn = sqlite3.connect(DATABASE_VENTAS)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ventas WHERE id = ?', (venta_id,))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Venta eliminada correctamente"})

# Ruta para obtener todas las ventas (API)
@app.route('/ventas')
def ventas():
    conn = sqlite3.connect(DATABASE_VENTAS)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ventas')
    ventas = cursor.fetchall()
    conn.close()
    return jsonify(ventas)

# Ruta para la página de ventas (formulario de contacto)
@app.route('/ventass', methods=['GET', 'POST'])
def ventass():
    if request.method == 'POST':
        # Obtener los datos del formulario de contacto
        nombre = request.form['name']
        correo = request.form['email']
        mensaje = request.form['message']

        # Guardar los datos en la base de datos
        with obtener_conexion_contactos() as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                INSERT INTO contactos (nombre, correo, mensaje) 
                VALUES (?, ?, ?) 
            ''', (nombre, correo, mensaje))
            conn.commit()

        flash("Tu mensaje ha sido enviado con éxito. Nos pondremos en contacto contigo pronto.", "success")
        return redirect(url_for('gracias'))

    return render_template('ventass.html')

# Ruta para la página de agradecimiento
@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash("Has cerrado sesión.", "info")
    return redirect(url_for('inicio'))

# Ruta para el paquete básico
@app.route('/paquete1')
def paquete1():
    return render_template('paquete1.html')  # Redirige a 'paquete1.html'

# Ruta para el paquete estándar
@app.route('/paquete2')
def paquete2():
    return render_template('paquete2.html')  # Redirige a 'paquete2.html'

# Ruta para el paquete premium
@app.route('/paquete3')
def paquete3():
    return render_template('paquete3.html')  # Redirige a 'paquete3.html'

if __name__ == '__main__':
    app.run(debug=True)
