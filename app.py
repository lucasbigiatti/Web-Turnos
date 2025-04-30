from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mail import Mail, Message
from datetime import datetime, timedelta, date, time
import os
from dotenv import load_dotenv
from models import Usuario, Paciente, Turno
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

from datetime import datetime  # Asegúrate de que esta importación esté presente

# Añade esta función a tu archivo app.py
@app.context_processor
def inject_now():
    return {'now': datetime.now()}



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
                
                # Intentar enviar correo de confirmación
                mensaje_email = ""
                
                # Crear un objeto turno simplificado para la notificación
                class TurnoTemp:
                    pass
                
                turno_obj = TurnoTemp()
                turno_obj.id = turno_id
                turno_obj.fecha = fecha
                turno_obj.hora = hora
                turno_obj.motivo = motivo
                turno_obj.estado = 'pendiente'
                
                if enviar_recordatorio_turno(turno_obj, paciente_info, 'confirmacion'):
                    mensaje_email = " Se ha enviado un correo de confirmación."
                
                flash(f'Turno para {nombre_paciente} agendado exitosamente para el {fecha_str} a las {hora_str}.{mensaje_email}', 'success')
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
    try:
        # Obtener el turno directamente de la base de datos
        query_turno = """
        SELECT t.*, p.nombre, p.apellido 
        FROM turnos t
        JOIN pacientes p ON t.paciente_id = p.id
        WHERE t.id = %s
        """
        result = db.execute_query(query_turno, (id_turno,))
        
        if not result or len(result) == 0:
            flash('Turno no encontrado', 'danger')
            return redirect(url_for('dashboard'))
        
        turno = result[0]
        print(f"DEBUG - Turno cargado: {turno}, tipo de hora: {type(turno['hora'])}")
        
        # Obtener todos los pacientes para el selector
        pacientes = Paciente.obtener_todos()
        
        if request.method == 'POST':
            # Obtener datos del formulario
            paciente_id = request.form.get('paciente_id')
            fecha_str = request.form.get('fecha')
            hora_str = request.form.get('hora')
            motivo = request.form.get('motivo')
            estado = request.form.get('estado')
            
            print(f"DEBUG - Datos del formulario - fecha: {fecha_str}, hora: {hora_str}")
            
            # Convertir strings a objetos date y time
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
            hora = datetime.strptime(hora_str, '%H:%M').time() if hora_str else None
            
            # Actualizar turno en la base de datos
            query = """
            UPDATE turnos 
            SET paciente_id = %s, fecha = %s, hora = %s, motivo = %s, estado = %s
            WHERE id = %s
            """
            params = (paciente_id, fecha, hora, motivo, estado, id_turno)
            
            db.execute_update(query, params)
            
            flash('Turno actualizado exitosamente', 'success')
            return redirect(url_for('dashboard'))
        
        # Si es GET, obtener el paciente del turno
        paciente_seleccionado = Paciente.obtener_por_id(turno['paciente_id'])
        
        # Formatear fecha para el formulario
        if isinstance(turno['fecha'], date):
            turno['fecha_form'] = turno['fecha'].strftime('%Y-%m-%d')
        else:
            try:
                fecha_obj = datetime.strptime(str(turno['fecha']), '%Y-%m-%d').date()
                turno['fecha_form'] = fecha_obj.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                try:
                    fecha_obj = datetime.strptime(str(turno['fecha']), '%d/%m/%Y').date()
                    turno['fecha_form'] = fecha_obj.strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    turno['fecha_form'] = str(turno['fecha'])
        
        # Formatear hora para el formulario - CORRECCIÓN CLAVE AQUÍ
        if isinstance(turno['hora'], time):
            # Si es un objeto time de Python, formatearlo a HH:MM
            hora_str = turno['hora'].strftime('%H:%M')
            print(f"DEBUG - Tipo time, hora formateada: {hora_str}")
            turno['hora_form'] = hora_str
        elif isinstance(turno['hora'], str):
            # Si ya es una cadena, intentar formatearla según su formato actual
            if ':' in turno['hora']:
                parts = turno['hora'].split(':')
                if len(parts) >= 2:
                    # Extraer solo HH:MM de cualquier formato de hora
                    hora_str = f"{parts[0]}:{parts[1]}"
                    print(f"DEBUG - Tipo str con ':', hora formateada: {hora_str}")
                    turno['hora_form'] = hora_str
                else:
                    turno['hora_form'] = turno['hora']
            else:
                turno['hora_form'] = turno['hora']
        else:
            # Para otros tipos, usar repr y logear para diagnóstico
            print(f"DEBUG - Tipo desconocido: {type(turno['hora'])}, valor: {turno['hora']}")
            try:
                hora_str = str(turno['hora'])
                if ':' in hora_str:
                    parts = hora_str.split(':')
                    if len(parts) >= 2:
                        turno['hora_form'] = f"{parts[0]}:{parts[1]}"
                    else:
                        turno['hora_form'] = hora_str
                else:
                    turno['hora_form'] = hora_str
            except:
                turno['hora_form'] = ""
        
        # Log para diagnóstico
        print(f"DEBUG - Valores formateados - fecha_form: {turno.get('fecha_form')}, hora_form: {turno.get('hora_form')}")
        
        # Mostrar formulario de edición con los valores formateados
        return render_template('editar_turno.html', 
                              turno=turno, 
                              paciente_seleccionado=paciente_seleccionado,
                              pacientes=pacientes)
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error al editar el turno: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/turnos/cancelar/<int:id_turno>', methods=['POST'])
def cancelar_turno(id_turno):
    """Cancela un turno."""
    try:
        # Verificar que el turno exista
        query_check = "SELECT * FROM turnos WHERE id = %s"
        result = db.execute_query(query_check, (id_turno,))
        
        if not result or len(result) == 0:
            flash('Turno no encontrado', 'danger')
            return redirect(url_for('dashboard'))
        
        # Actualizar el estado del turno a 'cancelado'
        query = "UPDATE turnos SET estado = 'cancelado' WHERE id = %s"
        db.execute_update(query, (id_turno,))
        
        # Obtener información del turno para el mensaje
        paciente_id = result[0]['paciente_id']
        paciente = Paciente.obtener_por_id(paciente_id)
        paciente_nombre = f"{paciente.nombre} {paciente.apellido}" if paciente else "desconocido"
        
        flash(f'Turno de {paciente_nombre} cancelado exitosamente', 'success')
        
        # Redireccionar de vuelta a la página desde donde se realizó la acción
        referer = request.headers.get('Referer')
        if referer and 'lista_turnos' in referer:
            return redirect(url_for('lista_turnos'))
        else:
            return redirect(url_for('dashboard'))
    
    except Exception as e:
        flash(f'Error al cancelar el turno: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

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
    """Cambia el estado de un turno."""
    try:
        # Verificar que el estado sea válido
        estados_validos = ['pendiente', 'confirmado', 'completado', 'cancelado']
        if estado not in estados_validos:
            return jsonify({'success': False, 'error': 'Estado no válido'})
        
        # Obtener información del turno y paciente antes de actualizar
        query_info = """
        SELECT t.*, p.id as pid, p.nombre, p.apellido, p.email, p.telefono, p.dni
        FROM turnos t
        JOIN pacientes p ON t.paciente_id = p.id
        WHERE t.id = %s
        """
        turno_info = db.execute_query(query_info, (id_turno,))
        
        if not turno_info or len(turno_info) == 0:
            return jsonify({'success': False, 'error': 'Turno no encontrado'})
            
        turno_data = turno_info[0]
        
        # Actualizar el estado en la base de datos
        query = "UPDATE turnos SET estado = %s WHERE id = %s"
        result = db.execute_update(query, (estado, id_turno))
        
        if result is not None:
            print(f"Turno {id_turno} cambiado a estado {estado}")
            
            # Si el estado es confirmado o cancelado, enviar notificación
            if estado in ['confirmado', 'cancelado']:
                # Crear objetos para la notificación
                class TurnoTemp:
                    pass
                
                class PacienteTemp:
                    pass
                
                turno_obj = TurnoTemp()
                turno_obj.id = turno_data['id']
                turno_obj.fecha = turno_data['fecha']
                turno_obj.hora = turno_data['hora']
                turno_obj.motivo = turno_data['motivo']
                turno_obj.estado = estado
                
                paciente_obj = PacienteTemp()
                paciente_obj.id = turno_data['pid']
                paciente_obj.nombre = turno_data['nombre']
                paciente_obj.apellido = turno_data['apellido']
                paciente_obj.email = turno_data['email']
                paciente_obj.dni = turno_data['dni']
                
                # Enviar correo
                enviar_recordatorio_turno(turno_obj, paciente_obj, 'cambio_estado')
            
            return jsonify({'success': True})
        else:
            print(f"Error al cambiar estado del turno {id_turno}")
            return jsonify({'success': False, 'error': 'Error al actualizar la base de datos'})
    except Exception as e:
        print(f"Excepción al cambiar estado del turno: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/test-email/<int:id_paciente>')
def test_email(id_paciente):
    """Ruta para probar el envío de emails."""
    try:
        # Obtener información del paciente
        paciente = Paciente.obtener_por_id(id_paciente)
        
        if not paciente:
            flash('Paciente no encontrado', 'danger')
            return redirect(url_for('dashboard'))
        
        # Crear un turno de prueba
        class TurnoTemp:
            pass
        
        turno = TurnoTemp()
        turno.fecha = date.today() + timedelta(days=1)
        turno.hora = time(10, 0)
        turno.motivo = "Prueba de correo electrónico"
        turno.estado = "confirmado"
        
        # Intentar enviar el correo
        if enviar_recordatorio_turno(turno, paciente, 'confirmacion'):
            flash(f'Correo enviado exitosamente a {paciente.email}', 'success')
        else:
            flash(f'Error al enviar correo a {paciente.email}', 'danger')
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error al probar envío de correo: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))    



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





def enviar_recordatorio_turno(turno, paciente, tipo='confirmacion'):
    """
    Envía un correo electrónico relacionado con un turno.
    
    Tipos:
    - confirmacion: cuando se crea un nuevo turno
    - recordatorio: para recordar un turno próximo
    - cambio_estado: cuando cambia el estado del turno
    """
    # Si no hay configuración de correo, no enviamos nada
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        print("No se ha configurado el correo electrónico")
        return False
    
    # Si el paciente no tiene email, no podemos enviar
    if not hasattr(paciente, 'email') or not paciente.email:
        print(f"El paciente no tiene email registrado")
        return False
    
    try:
        # Formatear fecha y hora para el mensaje
        if isinstance(turno.fecha, date):
            fecha_formateada = turno.fecha.strftime('%A %d de %B de %Y').capitalize()
        else:
            try:
                fecha_obj = datetime.strptime(str(turno.fecha), '%Y-%m-%d').date()
                fecha_formateada = fecha_obj.strftime('%A %d de %B de %Y').capitalize()
            except:
                fecha_formateada = str(turno.fecha)
            
        if isinstance(turno.hora, time):
            hora_formateada = turno.hora.strftime('%H:%M')
        else:
            try:
                if ':' in str(turno.hora):
                    partes = str(turno.hora).split(':')
                    hora_formateada = f"{partes[0]}:{partes[1]}"
                else:
                    hora_formateada = str(turno.hora)
            except:
                hora_formateada = str(turno.hora)
        
        # Definir asunto y cuerpo según el tipo
        if tipo == 'confirmacion':
            asunto = f'Confirmación de Turno - {fecha_formateada}'
            cuerpo = f"""
            Hola {paciente.nombre},
            
            Se ha agendado un turno para usted:
            
            Fecha: {fecha_formateada}
            Hora: {hora_formateada}
            Motivo: {turno.motivo if hasattr(turno, 'motivo') else 'No especificado'}
            
            Por favor, confirme su asistencia o avise con anticipación en caso de no poder asistir.
            
            Saludos cordiales,
            Sistema de Gestión de Turnos
            """
        elif tipo == 'cambio_estado':
            asunto = f'Actualización de Turno - {fecha_formateada}'
            estado_str = {'pendiente': 'pendiente de confirmación', 
                          'confirmado': 'confirmado', 
                          'completado': 'completado', 
                          'cancelado': 'cancelado'}.get(turno.estado, str(turno.estado))
            
            cuerpo = f"""
            Hola {paciente.nombre},
            
            Le informamos que el estado de su turno ha cambiado a: {estado_str.upper()}
            
            Detalles del turno:
            Fecha: {fecha_formateada}
            Hora: {hora_formateada}
            Motivo: {turno.motivo if hasattr(turno, 'motivo') else 'No especificado'}
            
            Saludos cordiales,
            Sistema de Gestión de Turnos
            """
        else:
            asunto = f'Información sobre su Turno - {fecha_formateada}'
            cuerpo = f"""
            Hola {paciente.nombre},
            
            Información sobre su turno:
            
            Fecha: {fecha_formateada}
            Hora: {hora_formateada}
            Motivo: {turno.motivo if hasattr(turno, 'motivo') else 'No especificado'}
            Estado: {turno.estado if hasattr(turno, 'estado') else 'No especificado'}
            
            Saludos cordiales,
            Sistema de Gestión de Turnos
            """
        
        # Crear y enviar el mensaje
        msg = Message(
            subject=asunto,
            recipients=[paciente.email],
            body=cuerpo
        )
        
        mail.send(msg)
        print(f"Correo enviado a {paciente.email}: {asunto}")
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        import traceback
        traceback.print_exc()
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
    

    


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)       