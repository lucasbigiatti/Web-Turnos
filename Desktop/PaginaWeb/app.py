from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mail import Mail, Message
from datetime import datetime, timedelta, date, time
import os
from dotenv import load_dotenv
from models import Usuario, Paciente, Turno, Configuracion
import calendar
import locale
from db_conexion import db

# Configurar el locale para español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Para sistemas Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Para Windows
    except:
        pass  # Si falla, se usará el locale por defecto

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave_secreta_por_defecto')

# Configuración de correo electrónico
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', '')

mail = Mail(app)



@app.before_request
def before_request():
    """Asegura que la conexión a la base de datos esté disponible antes de cada solicitud."""
    try:
        from db_conexion import db
        db.get_connection()  # Esto intentará reconectar si es necesario
    except Exception as e:
        print(f"Error de conexión a la base de datos: {e}")
        # Podrías redirigir a una página de error aquí si lo deseas


# Rutas principales
@app.route('/')
def index():
    # Evitamos la consulta de turnos que está causando problemas
    # Redirigimos directamente al dashboard
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    # Simulamos un usuario para desarrollo
    id_usuario = 1

    try:
        # Obtenemos datos para el dashboard
        fecha_actual = date.today()
        
        # Obtener turnos para hoy
        query_hoy = """
        SELECT t.*, p.nombre as paciente_nombre, p.apellido as paciente_apellido 
        FROM turnos t
        JOIN pacientes p ON t.paciente_id = p.id
        WHERE t.fecha = %s
        ORDER BY t.hora ASC
        """
        turnos_hoy_raw = db.execute_query(query_hoy, (fecha_actual,))
        
        # Formatear los datos de turnos_hoy
        turnos_hoy = []
        if turnos_hoy_raw:
            for turno in turnos_hoy_raw:
                turnos_hoy.append({
                    'id': turno['id'],
                    'paciente_nombre': f"{turno['paciente_nombre']} {turno['paciente_apellido']}",
                    'hora': turno['hora'].strftime('%H:%M') if isinstance(turno['hora'], time) else turno['hora'],
                    'motivo': turno['motivo'],
                    'estado': turno['estado']
                })
        
        # Obtener próximos turnos (excluyendo hoy)
        query_proximos = """
        SELECT t.*, p.nombre as paciente_nombre, p.apellido as paciente_apellido 
        FROM turnos t
        JOIN pacientes p ON t.paciente_id = p.id
        WHERE t.fecha > %s
        ORDER BY t.fecha ASC, t.hora ASC
        LIMIT 10
        """
        proximos_turnos_raw = db.execute_query(query_proximos, (fecha_actual,))
        
        # Formatear los datos de proximos_turnos
        proximos_turnos = []
        if proximos_turnos_raw:
            for turno in proximos_turnos_raw:
                proximos_turnos.append({
                    'id': turno['id'],
                    'paciente_nombre': f"{turno['paciente_nombre']} {turno['paciente_apellido']}",
                    'fecha': turno['fecha'].strftime('%d/%m/%Y') if isinstance(turno['fecha'], date) else turno['fecha'],
                    'hora': turno['hora'].strftime('%H:%M') if isinstance(turno['hora'], time) else turno['hora'],
                    'motivo': turno['motivo'],
                    'estado': turno['estado']
                })
        
        # Contadores
        total_pendientes = sum(1 for t in turnos_hoy if t['estado'] == 'pendiente')
        total_pendientes += sum(1 for t in proximos_turnos if t['estado'] == 'pendiente')
        
        total_confirmados = sum(1 for t in turnos_hoy if t['estado'] == 'confirmado')
        total_confirmados += sum(1 for t in proximos_turnos if t['estado'] == 'confirmado')
        
        # Obtener total de pacientes
        query_pacientes = "SELECT COUNT(*) as total FROM pacientes"
        resultado_pacientes = db.execute_query(query_pacientes)
        total_pacientes = resultado_pacientes[0]['total'] if resultado_pacientes else 0
        
        return render_template('dashboard.html', 
                              turnos_hoy=turnos_hoy, 
                              proximos_turnos=proximos_turnos,
                              total_pendientes=total_pendientes,
                              total_confirmados=total_confirmados,
                              total_pacientes=total_pacientes,
                              fecha_actual=fecha_actual)
    except Exception as e:
        print(f"Error en dashboard: {e}")
        import traceback
        traceback.print_exc()
        # En caso de error, mostrar dashboard vacío
        return render_template('dashboard.html', 
                              turnos_hoy=[], 
                              proximos_turnos=[],
                              total_pendientes=0,
                              total_confirmados=0,
                              total_pacientes=0,
                              fecha_actual=date.today())
# Rutas para Pacientes
@app.route('/pacientes')
def lista_pacientes():
    pacientes = Paciente.obtener_todos()
    return render_template('pacientes.html', pacientes=pacientes)

@app.route('/pacientes/nuevo', methods=['GET', 'POST'])
def nuevo_paciente():
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        dni = request.form.get('dni')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        obra_social = request.form.get('obra_social')
        numero_afiliado = request.form.get('numero_afiliado')
        
        # Crear un nuevo paciente
        paciente = Paciente(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            email=email,
            telefono=telefono,
            fecha_nacimiento=fecha_nacimiento,
            obra_social=obra_social,
            numero_afiliado=numero_afiliado
        )
        
        # Guardar el paciente en la base de datos
        paciente.guardar()
        
        # Redireccionar a la lista de pacientes
        flash('Paciente agregado exitosamente', 'success')
        return redirect(url_for('lista_pacientes'))
    
    # Si es una solicitud GET, mostrar el formulario
    return render_template('pacientes.html', modo='nuevo')

@app.route('/pacientes/editar/<int:id_paciente>', methods=['GET', 'POST'])
def editar_paciente(id_paciente):
    """Edita los datos de un paciente."""
    paciente = Paciente.obtener_por_id(id_paciente)
    
    if not paciente:
        flash('Paciente no encontrado', 'danger')
        return redirect(url_for('lista_pacientes'))
    
    if request.method == 'POST':
        # Obtener datos del formulario
        paciente.nombre = request.form.get('nombre')
        paciente.apellido = request.form.get('apellido')
        paciente.dni = request.form.get('dni')
        paciente.email = request.form.get('email')
        paciente.telefono = request.form.get('telefono')
        paciente.fecha_nacimiento = request.form.get('fecha_nacimiento')
        paciente.obra_social = request.form.get('obra_social')
        paciente.numero_afiliado = request.form.get('numero_afiliado')
        
        # Actualizar en la base de datos
        query = """
        UPDATE pacientes 
        SET nombre = %s, apellido = %s, dni = %s, email = %s, 
            telefono = %s, fecha_nacimiento = %s, obra_social = %s, numero_afiliado = %s
        WHERE id = %s
        """
        params = (
            paciente.nombre, paciente.apellido, paciente.dni, paciente.email,
            paciente.telefono, paciente.fecha_nacimiento, paciente.obra_social,
            paciente.numero_afiliado, id_paciente
        )
        
        db.execute_update(query, params)
        
        flash(f'Paciente "{paciente.nombre} {paciente.apellido}" actualizado exitosamente', 'success')
        return redirect(url_for('lista_pacientes'))
        
    # Si es GET, mostrar formulario para editar
    return render_template('pacientes.html', paciente=paciente, modo='editar')

@app.route('/pacientes/eliminar/<int:id_paciente>', methods=['POST'])
def eliminar_paciente(id_paciente):
    """Elimina un paciente de la base de datos."""
    # Primero obtenemos el paciente para confirmar que existe
    paciente = Paciente.obtener_por_id(id_paciente)
    
    if paciente:
        # Ejecutar eliminación en la base de datos
        query = "DELETE FROM pacientes WHERE id = %s"
        db.execute_update(query, (id_paciente,))
        flash(f'Paciente "{paciente.nombre} {paciente.apellido}" eliminado exitosamente', 'success')
    else:
        flash('Paciente no encontrado', 'danger')
        
    return redirect(url_for('lista_pacientes'))

@app.route('/pacientes/buscar')
def buscar_pacientes():
    termino = request.args.get('termino', '')
    if termino:
        pacientes = Paciente.buscar(termino)
    else:
        pacientes = Paciente.obtener_todos()
    
    return render_template('pacientes.html', pacientes=pacientes, termino_busqueda=termino)

@app.route('/calendario')
def calendario():
    # Get month and year from query parameters or use current date
    mes = request.args.get('mes', type=int)
    anio = request.args.get('anio', type=int)
    
    # If month or year not provided, use current date
    now = datetime.now()
    if mes is None:
        mes = now.month
    if anio is None:
        anio = now.year
    
    # Handle month overflow/underflow
    if mes > 12:
        mes = 1
        anio += 1
    elif mes < 1:
        mes = 12
        anio -= 1
    
    # Get month name in Spanish
    try:
        nombre_mes = date(anio, mes, 1).strftime('%B').capitalize()
    except:
        nombre_mes = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][mes-1]
    
    # Create calendar data
    cal = calendar.monthcalendar(anio, mes)
    
    # Create dates dictionary for the calendar
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fechas_calendario = {dia: date(anio, mes, dia) for dia in range(1, ultimo_dia + 1)}
    
    # Check which date is today
    hoy = date.today()
    
    return render_template(
        'calendario.html',
        calendario=cal,
        fechas_calendario=fechas_calendario,
        hoy=hoy,
        mes=mes,
        anio=anio,
        nombre_mes=nombre_mes
    )





@app.route('/turnos/nuevo', methods=['GET', 'POST'])
def nuevo_turno():
    """Crea un nuevo turno."""
    # Verificar si se recibió un id_paciente en la URL
    id_paciente = request.args.get('id_paciente', None)
    paciente = None
    
    if id_paciente:
        paciente = Paciente.obtener_por_id(id_paciente)
    
    # Obtener todos los pacientes para el selector
    pacientes = Paciente.obtener_todos()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            paciente_id = request.form.get('paciente_id')
            fecha_str = request.form.get('fecha')
            hora_str = request.form.get('hora')
            motivo = request.form.get('motivo')
            
            # Convertir strings a objetos date y time
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
            hora = datetime.strptime(hora_str, '%H:%M').time() if hora_str else None
            
            # Insertar directamente en la base de datos
            query = """
            INSERT INTO turnos (paciente_id, fecha, hora, motivo, estado)
            VALUES (%s, %s, %s, %s, 'pendiente')
            """
            params = (paciente_id, fecha, hora, motivo)
            
            turno_id = db.execute_update(query, params)
            
            if turno_id:
                # Obtener el nombre del paciente para el mensaje
                paciente_info = Paciente.obtener_por_id(paciente_id)
                nombre_paciente = f"{paciente_info.nombre} {paciente_info.apellido}" if paciente_info else "desconocido"
                
                flash(f'Turno para {nombre_paciente} agendado exitosamente para el {fecha_str} a las {hora_str}', 'success')
                return redirect(url_for('lista_turnos'))
            else:
                flash('Error al agendar el turno', 'danger')
        except Exception as e:
            flash(f'Error al agendar el turno: {str(e)}', 'danger')
    
    # Si es GET o hubo un error
    return render_template('turnos.html', modo='nuevo', paciente_seleccionado=paciente, pacientes=pacientes)

@app.route('/turnos/editar/<int:id_turno>', methods=['GET', 'POST'])
def editar_turno(id_turno):
    """Edita un turno existente."""
    # Obtener el turno
    query_turno = "SELECT * FROM turnos WHERE id = %s"
    result = db.execute_query(query_turno, (id_turno,))
    
    if not result or len(result) == 0:
        flash('Turno no encontrado', 'danger')
        return redirect(url_for('lista_turnos'))
    
    turno = result[0]
    
    # Obtener todos los pacientes para el selector
    pacientes = Paciente.obtener_todos()
    
    if request.method == 'POST':
        # Obtener datos del formulario
        paciente_id = request.form.get('paciente_id')
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        motivo = request.form.get('motivo')
        estado = request.form.get('estado')
        
        # Actualizar turno en la base de datos
        query = """
        UPDATE turnos 
        SET paciente_id = %s, fecha = %s, hora = %s, motivo = %s, estado = %s
        WHERE id = %s
        """
        params = (paciente_id, fecha, hora, motivo, estado, id_turno)
        
        db.execute_update(query, params)
        
        flash('Turno actualizado exitosamente', 'success')
        return redirect(url_for('lista_turnos'))
    
    # Si es GET, obtener el paciente del turno
    paciente_seleccionado = Paciente.obtener_por_id(turno['paciente_id'])
    
    # Mostrar formulario de edición
    return render_template('editar_turno.html', 
                          turno=turno, 
                          paciente_seleccionado=paciente_seleccionado,
                          pacientes=pacientes)

@app.route('/turnos/cancelar/<int:id_turno>', methods=['POST'])
def cancelar_turno(id_turno):
    """Cancela un turno."""
    # Actualizar el estado del turno a 'cancelado'
    query = "UPDATE turnos SET estado = 'cancelado' WHERE id = %s"
    db.execute_update(query, (id_turno,))
    
    flash('Turno cancelado exitosamente', 'success')
    return redirect(url_for('lista_turnos'))

@app.route('/turnos/eliminar/<int:id_turno>', methods=['POST'])
def eliminar_turno(id_turno):
    turno = Turno.obtener_por_id(id_turno)
    
    if not turno:
        flash('Turno no encontrado', 'error')
        return redirect(url_for('calendario'))
    
    # Guardar la fecha antes de eliminar para redirigir al mismo mes
    fecha = turno.fecha
    
    if turno.eliminar():
        flash('Turno eliminado exitosamente', 'success')
    else:
        flash('Error al eliminar el turno', 'error')
    
    return redirect(url_for('calendario', mes=fecha.month, anio=fecha.year))

@app.route('/turnos/cambiar_estado/<int:id_turno>/<estado>', methods=['POST'])
def cambiar_estado_turno(id_turno, estado):
    turno = Turno.obtener_por_id(id_turno)
    
    if not turno:
        return jsonify({'success': False, 'error': 'Turno no encontrado'})
    
    if turno.cambiar_estado(estado):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Error al cambiar el estado'})
    
@app.route('/turnos')
def lista_turnos():
    """Muestra la lista de turnos."""
    # Obtener todos los turnos con información del paciente
    query = """
    SELECT t.*, p.nombre, p.apellido 
    FROM turnos t
    JOIN pacientes p ON t.paciente_id = p.id
    ORDER BY t.fecha ASC, t.hora ASC
    """
    
    turnos = db.execute_query(query)
    
    return render_template('turnos.html', turnos=turnos, modo='lista')





# Rutas para configuración
@app.route('/configuracion', methods=['GET', 'POST'])
def configuracion():
    # Simulamos un usuario para desarrollo
    id_usuario = 1
    
    # Obtener la configuración actual
    config = Configuracion.obtener_por_usuario(id_usuario)
    
    # Convertir timedeltas a strings formateados para la vista
    if config.horario_inicio:
        total_seconds = config.horario_inicio.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        config.horario_inicio_str = f"{hours:02d}:{minutes:02d}"
    else:
        config.horario_inicio_str = "09:00"
        
    if config.horario_fin:
        total_seconds = config.horario_fin.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        config.horario_fin_str = f"{hours:02d}:{minutes:02d}"
    else:
        config.horario_fin_str = "18:00"
    
    if request.method == 'POST':
        # Actualizar configuración
        horario_inicio_str = request.form.get('horario_inicio')
        horario_fin_str = request.form.get('horario_fin')
        duracion_turno = int(request.form.get('duracion_turno', 30))
        
        # Convertir horarios de string a time
        try:
            hora_inicio = datetime.strptime(horario_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(horario_fin_str, '%H:%M').time()
            
            # Convertir time a timedelta para almacenar
            config.horario_inicio = timedelta(hours=hora_inicio.hour, minutes=hora_inicio.minute)
            config.horario_fin = timedelta(hours=hora_fin.hour, minutes=hora_fin.minute)
        except ValueError:
            flash('Formato de hora incorrecto', 'error')
            return redirect(url_for('configuracion'))
        
        config.duracion_turno = duracion_turno
        
        if config.guardar():
            flash('Configuración guardada exitosamente', 'success')
            
            # Actualizar los strings formateados después de guardar
            if config.horario_inicio:
                total_seconds = config.horario_inicio.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                config.horario_inicio_str = f"{hours:02d}:{minutes:02d}"
                
            if config.horario_fin:
                total_seconds = config.horario_fin.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                config.horario_fin_str = f"{hours:02d}:{minutes:02d}"
        else:
            flash('Error al guardar la configuración', 'error')
    
    return render_template('configuracion.html', config=config)

# Función para enviar recordatorios por email
def enviar_recordatorio_turno(turno, paciente):
    # Si no hay configuración de correo, no enviamos nada
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        return False
    
    # Obtener datos del profesional
    profesional = Usuario.obtener_por_id(turno.id_usuario)
    
    # Formatear fecha y hora para el mensaje
    fecha_formateada = turno.fecha.strftime('%A %d de %B de %Y').capitalize()
    hora_formateada = turno.hora.strftime('%H:%M')
    
    # Crear el mensaje
    asunto = f'Confirmación de Turno - {fecha_formateada}'
    
    cuerpo = f"""
    Hola {paciente.nombre},
    
    Este es un recordatorio de su turno programado:
    
    Fecha: {fecha_formateada}
    Hora: {hora_formateada}
    Profesional: {profesional.nombre if profesional else 'No especificado'}
    
    Por favor, confirme su asistencia o avise con anticipación en caso de no poder asistir.
    
    Saludos cordiales,
    Sistema de Gestión de Turnos
    """
    
    msg = Message(
        subject=asunto,
        recipients=[paciente.email],
        body=cuerpo
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

# API para obtener horarios disponibles
@app.route('/api/horarios_disponibles', methods=['GET'])
def api_horarios_disponibles():
    fecha_str = request.args.get('fecha')
    id_usuario = request.args.get('id_usuario', 1)  # Por defecto usamos el usuario 1
    
    # Convertir fecha de string a date
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Formato de fecha incorrecto'}), 400
    
    # Obtener configuración del profesional
    config = Configuracion.obtener_por_usuario(id_usuario)
    
    # Convertir timedeltas a time objects
    if config.horario_inicio:
        total_seconds = config.horario_inicio.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        horario_inicio = time(hours, minutes)
    else:
        horario_inicio = time(9, 0)  # 9:00 AM default
        
    if config.horario_fin:
        total_seconds = config.horario_fin.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        horario_fin = time(hours, minutes)
    else:
        horario_fin = time(18, 0)  # 6:00 PM default
    
    # Obtener turnos existentes para esa fecha y usuario
    turnos_ocupados = Turno.obtener_por_fecha_y_usuario(fecha, id_usuario)
    horas_ocupadas = [turno.hora for turno in turnos_ocupados]
    
    # Generar todos los horarios posibles según la configuración
    horarios_disponibles = []
    
    # Convertir a datetime para poder hacer aritmética con timedelta
    dt_inicio = datetime.combine(fecha, horario_inicio)
    dt_fin = datetime.combine(fecha, horario_fin)
    duracion = timedelta(minutes=config.duracion_turno or 30)
    
    current = dt_inicio
    while current + duracion <= dt_fin:
        # Si la hora actual no está ocupada, la agregamos como disponible
        if current.time() not in horas_ocupadas:
            horarios_disponibles.append(current.strftime('%H:%M'))
        current += duracion
    
    return jsonify({
        'fecha': fecha_str,
        'horarios_disponibles': horarios_disponibles
    })

# Función para inicializar la base de datos con datos de ejemplo
@app.route('/inicializar_db', methods=['GET'])
def inicializar_db():
    # Crear usuarios/profesionales de ejemplo
    usuario1 = Usuario(
        nombre="Dr. Juan Pérez",
        email="juan.perez@ejemplo.com",
        telefono="123456789",
        especialidad="Medicina General"
    )
    usuario1.guardar()
    
    # Crear configuración para el usuario
    config = Configuracion(
        id_usuario=1,  # ID del usuario recién creado
        horario_inicio=timedelta(hours=9),  # 9:00 AM
        horario_fin=timedelta(hours=17),    # 5:00 PM
        duracion_turno=30           # 30 minutos
    )
    config.guardar()
    
    # Crear pacientes de ejemplo
    paciente1 = Paciente(
        nombre="María González",
        email="maria@ejemplo.com",
        telefono="987654321",
        fecha_nacimiento=date(1985, 5, 15)
    )
    paciente1.guardar()
    
    paciente2 = Paciente(
        nombre="Carlos Rodríguez",
        email="carlos@ejemplo.com",
        telefono="555123456",
        fecha_nacimiento=date(1990, 10, 20)
    )
    paciente2.guardar()
    
    # Crear algunos turnos de ejemplo
    hoy = date.today()
    manana = hoy + timedelta(days=1)
    
    turno1 = Turno(
        id_paciente=1,
        id_usuario=1,
        fecha=hoy,
        hora=time(10, 0),
        estado="confirmado",
        notas="Primera consulta"
    )
    turno1.guardar()
    
    turno2 = Turno(
        id_paciente=2,
        id_usuario=1,
        fecha=manana,
        hora=time(11, 0),
        estado="pendiente",
        notas="Control de rutina"
    )
    turno2.guardar()
    
    flash('Base de datos inicializada con datos de ejemplo', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)