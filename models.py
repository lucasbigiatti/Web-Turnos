from db_conexion import DatabaseConnection
from datetime import datetime, date, time
from db_conexion import db

class Usuario:
    def __init__(self, id_usuario=None, nombre=None, email=None, telefono=None, especialidad=None):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.email = email
        self.telefono = telefono
        self.especialidad = especialidad
        self.db = DatabaseConnection()
    
    def guardar(self):
        """Guarda o actualiza un usuario en la base de datos."""
        if self.id_usuario:
            # Actualizar usuario existente
            query = """
                UPDATE usuarios 
                SET nombre = %s, email = %s, telefono = %s, especialidad = %s 
                WHERE id_usuario = %s
            """
            params = (self.nombre, self.email, self.telefono, self.especialidad, self.id_usuario)
            return self.db.execute_query(query, params)
        else:
            # Insertar nuevo usuario
            query = """
                INSERT INTO usuarios (nombre, email, telefono, especialidad) 
                VALUES (%s, %s, %s, %s)
            """
            params = (self.nombre, self.email, self.telefono, self.especialidad)
            result = self.db.execute_query(query, params)
            if result:
                self.id_usuario = result
            return result
    
    def eliminar(self):
        """Elimina un usuario de la base de datos."""
        if not self.id_usuario:
            return False
            
        query = "DELETE FROM usuarios WHERE id_usuario = %s"
        return self.db.execute_query(query, (self.id_usuario,))
    
    @classmethod
    def obtener_por_id(cls, id_usuario):
        """Obtiene un usuario por su ID."""
        db = DatabaseConnection()
        query = "SELECT * FROM usuarios WHERE id_usuario = %s"
        result = db.execute_query(query, (id_usuario,))
        
        if result and isinstance(result, list) and len(result) > 0:
            usuario_data = result[0]
            return cls(
                id_usuario=usuario_data['id_usuario'],
                nombre=usuario_data['nombre'],
                email=usuario_data['email'],
                telefono=usuario_data['telefono'],
                especialidad=usuario_data['especialidad']
            )
        return None
    
    @classmethod
    def obtener_todos(cls):
        """Obtiene todos los usuarios."""
        db = DatabaseConnection()
        query = "SELECT * FROM usuarios ORDER BY nombre"
        result = db.execute_query(query)
        
        usuarios = []
        if result and isinstance(result, list):
            for usuario_data in result:
                usuarios.append(cls(
                    id_usuario=usuario_data['id_usuario'],
                    nombre=usuario_data['nombre'],
                    email=usuario_data['email'],
                    telefono=usuario_data['telefono'],
                    especialidad=usuario_data['especialidad']
                ))
        return usuarios


class Paciente:
    def __init__(self, nombre, apellido, dni, email=None, telefono=None, 
                 fecha_nacimiento=None, obra_social=None, numero_afiliado=None, id=None):
        self.id = id  # Usamos id en lugar de id_paciente
        self.nombre = nombre
        self.apellido = apellido
        self.dni = dni
        self.email = email
        self.telefono = telefono
        self.fecha_nacimiento = fecha_nacimiento
        self.obra_social = obra_social
        self.numero_afiliado = numero_afiliado
        
        # Para compatibilidad con el código existente que usa id_paciente
        self.id_paciente = id
        
    def guardar(self):
        """Guarda el paciente en la base de datos."""
        query = """
        INSERT INTO pacientes 
        (nombre, apellido, dni, email, telefono, fecha_nacimiento, obra_social, numero_afiliado) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            self.nombre, 
            self.apellido, 
            self.dni, 
            self.email, 
            self.telefono, 
            self.fecha_nacimiento, 
            self.obra_social, 
            self.numero_afiliado
        )
        
        # Guardar y obtener el id generado
        last_id = db.execute_update(query, params)
        if last_id:
            self.id = last_id
            self.id_paciente = last_id  # Para compatibilidad
        return last_id
        
    @classmethod
    def obtener_todos(cls):
        """Obtiene todos los pacientes de la base de datos."""
        query = "SELECT * FROM pacientes"
        result = db.execute_query(query)
        
        pacientes = []
        if result:
            for paciente_data in result:
                paciente = cls(
                    nombre=paciente_data['nombre'],
                    apellido=paciente_data['apellido'],
                    dni=paciente_data['dni'],
                    email=paciente_data['email'],
                    telefono=paciente_data['telefono'],
                    fecha_nacimiento=paciente_data['fecha_nacimiento'],
                    obra_social=paciente_data['obra_social'],
                    numero_afiliado=paciente_data['numero_afiliado'],
                    id=paciente_data['id']  # Usamos id de la base de datos
                )
                # Para compatibilidad con el código que espera id_paciente
                paciente.id_paciente = paciente_data['id']
                pacientes.append(paciente)
        
        return pacientes
    
    @classmethod
    def obtener_por_id(cls, id_paciente):
        """Obtiene un paciente por su ID."""
        query = "SELECT * FROM pacientes WHERE id = %s"
        result = db.execute_query(query, (id_paciente,))
        
        if result and len(result) > 0:
            paciente_data = result[0]
            paciente = cls(
                nombre=paciente_data['nombre'],
                apellido=paciente_data['apellido'],
                dni=paciente_data['dni'],
                email=paciente_data['email'],
                telefono=paciente_data['telefono'],
                fecha_nacimiento=paciente_data['fecha_nacimiento'],
                obra_social=paciente_data['obra_social'],
                numero_afiliado=paciente_data['numero_afiliado'],
                id=paciente_data['id']
            )
            # Para compatibilidad
            paciente.id_paciente = paciente_data['id']
            return paciente
        return None












class Turno:
    def __init__(self, id_turno=None, id_paciente=None, id_usuario=None, fecha=None, 
                 hora=None, estado="pendiente", notas=None):
        self.id_turno = id_turno
        self.id_paciente = id_paciente
        self.id_usuario = id_usuario
        self.fecha = fecha
        self.hora = hora
        self.estado = estado
        self.notas = notas
        self.db = DatabaseConnection()
        # Atributos opcionales para mostrar información relacionada
        self.paciente_nombre = None
        self.usuario_nombre = None
    
    def guardar(self):
        """Guarda o actualiza un turno en la base de datos."""
        if self.id_turno:
            # Actualizar turno existente
            query = """
                UPDATE turnos 
                SET id_paciente = %s, id_usuario = %s, fecha = %s, 
                    hora = %s, estado = %s, notas = %s 
                WHERE id_turno = %s
            """
            params = (
                self.id_paciente, self.id_usuario, self.fecha, self.hora, 
                self.estado, self.notas, self.id_turno
            )
            return self.db.execute_query(query, params)
        else:
            # Insertar nuevo turno
            query = """
                INSERT INTO turnos 
                (id_paciente, id_usuario, fecha, hora, estado, notas) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (
                self.id_paciente, self.id_usuario, self.fecha, 
                self.hora, self.estado, self.notas
            )
            result = self.db.execute_query(query, params)
            if result:
                self.id_turno = result
            return result
    
    def eliminar(self):
        """Elimina un turno de la base de datos."""
        if not self.id_turno:
            return False
            
        query = "DELETE FROM turnos WHERE id_turno = %s"
        return self.db.execute_query(query, (self.id_turno,))
    
    def cambiar_estado(self, nuevo_estado):
        """Cambia el estado de un turno."""
        estados_validos = ['pendiente', 'confirmado', 'cancelado', 'atendido']
        if nuevo_estado not in estados_validos:
            return False
            
        self.estado = nuevo_estado
        return self.guardar()
    
    @classmethod
    def obtener_por_id(cls, id_turno):
        """Obtiene un turno por su ID con datos de paciente y profesional."""
        db = DatabaseConnection()
        query = """
            SELECT t.*, p.nombre as paciente_nombre, u.nombre as usuario_nombre 
            FROM turnos t
            JOIN pacientes p ON t.id_paciente = p.id_paciente
            JOIN usuarios u ON t.id_usuario = u.id_usuario
            WHERE t.id_turno = %s
        """
        result = db.execute_query(query, (id_turno,))
        
        if result and isinstance(result, list) and len(result) > 0:
            turno_data = result[0]
            turno = cls(
                id_turno=turno_data['id_turno'],
                id_paciente=turno_data['id_paciente'],
                id_usuario=turno_data['id_usuario'],
                fecha=turno_data['fecha'],
                hora=turno_data['hora'],
                estado=turno_data['estado'],
                notas=turno_data['notas']
            )
            # Agregamos información relacionada
            turno.paciente_nombre = turno_data['paciente_nombre']
            turno.usuario_nombre = turno_data['usuario_nombre']
            return turno
        return None
    
    @classmethod
    def obtener_por_fecha_y_usuario(cls, fecha, id_usuario=None):
        """Obtiene todos los turnos para una fecha específica y opcionalmente de un usuario."""
        db = DatabaseConnection()
        
        # Debug
        print(f"Buscando turnos para fecha {fecha} y usuario {id_usuario}")
        
        if id_usuario:
            query = """
                SELECT t.*, p.nombre as paciente_nombre, u.nombre as usuario_nombre 
                FROM turnos t
                JOIN pacientes p ON t.id_paciente = p.id_paciente
                JOIN usuarios u ON t.id_usuario = u.id_usuario
                WHERE DATE(t.fecha) = %s AND t.id_usuario = %s
                ORDER BY t.hora
            """
            query_params = (fecha, id_usuario)
        else:
            query = """
                SELECT t.*, p.nombre as paciente_nombre, u.nombre as usuario_nombre 
                FROM turnos t
                JOIN pacientes p ON t.id_paciente = p.id_paciente
                JOIN usuarios u ON t.id_usuario = u.id_usuario
                WHERE DATE(t.fecha) = %s
                ORDER BY t.hora, u.nombre
            """
            query_params = (fecha,)
        
        result = db.execute_query(query, query_params)
        
        # Debug
        print(f"Resultado de la consulta: {result}")
        
        turnos = []
        if result and isinstance(result, list):
            for turno_data in result:
                turno = cls(
                    id_turno=turno_data['id_turno'],
                    id_paciente=turno_data['id_paciente'],
                    id_usuario=turno_data['id_usuario'],
                    fecha=turno_data['fecha'],
                    hora=turno_data['hora'],
                    estado=turno_data['estado'],
                    notas=turno_data['notas'] if 'notas' in turno_data else None
                )
                # Agregamos información relacionada
                turno.paciente_nombre = turno_data['paciente_nombre']
                turno.usuario_nombre = turno_data['usuario_nombre']
                turnos.append(turno)
        
        # Debug
        print(f"Turnos encontrados: {len(turnos)}")
        
        return turnos
    
    @classmethod
    def obtener_por_paciente(cls, id_paciente):
        """Obtiene todos los turnos de un paciente específico."""
        db = DatabaseConnection()
        query = """
            SELECT t.*, p.nombre as paciente_nombre, u.nombre as usuario_nombre 
            FROM turnos t
            JOIN pacientes p ON t.id_paciente = p.id_paciente
            JOIN usuarios u ON t.id_usuario = u.id_usuario
            WHERE t.id_paciente = %s
            ORDER BY t.fecha DESC, t.hora
        """
        result = db.execute_query(query, (id_paciente,))
        
        turnos = []
        if result and isinstance(result, list):
            for turno_data in result:
                turno = cls(
                    id_turno=turno_data['id_turno'],
                    id_paciente=turno_data['id_paciente'],
                    id_usuario=turno_data['id_usuario'],
                    fecha=turno_data['fecha'],
                    hora=turno_data['hora'],
                    estado=turno_data['estado'],
                    notas=turno_data['notas']
                )
                # Agregamos información relacionada
                turno.paciente_nombre = turno_data['paciente_nombre']
                turno.usuario_nombre = turno_data['usuario_nombre']
                turnos.append(turno)
        
        return turnos
    
    @classmethod
    def obtener_proximos(cls, id_usuario=None, limite=10):
        """Obtiene los próximos turnos, opcionalmente filtrando por profesional."""
        db = DatabaseConnection()
        
        # Debug
        print(f"Buscando próximos turnos para usuario {id_usuario}, límite {limite}")
        
        hoy = datetime.now().date()
        ahora = datetime.now().time()
        
        if id_usuario:
            query = """
                SELECT t.*, p.nombre as paciente_nombre, u.nombre as usuario_nombre 
                FROM turnos t
                JOIN pacientes p ON t.id_paciente = p.id_paciente
                JOIN usuarios u ON t.id_usuario = u.id_usuario
                WHERE (DATE(t.fecha) > %s OR (DATE(t.fecha) = %s AND t.hora >= %s))
                AND t.id_usuario = %s
                AND t.estado IN ('pendiente', 'confirmado')
                ORDER BY t.fecha, t.hora
                LIMIT %s
            """
            query_params = (hoy, hoy, ahora, id_usuario, limite)
        else:
            query = """
                SELECT t.*, p.nombre as paciente_nombre, u.nombre as usuario_nombre 
                FROM turnos t
                JOIN pacientes p ON t.id_paciente = p.id_paciente
                JOIN usuarios u ON t.id_usuario = u.id_usuario
                WHERE (DATE(t.fecha) > %s OR (DATE(t.fecha) = %s AND t.hora >= %s))
                AND t.estado IN ('pendiente', 'confirmado')
                ORDER BY t.fecha, t.hora
                LIMIT %s
            """
            query_params = (hoy, hoy, ahora, limite)
        
        result = db.execute_query(query, query_params)
        
        # Debug
        print(f"Resultado de la consulta: {result}")
        
        turnos = []
        if result and isinstance(result, list):
            for turno_data in result:
                turno = cls(
                    id_turno=turno_data['id_turno'],
                    id_paciente=turno_data['id_paciente'],
                    id_usuario=turno_data['id_usuario'],
                    fecha=turno_data['fecha'],
                    hora=turno_data['hora'],
                    estado=turno_data['estado'],
                    notas=turno_data['notas'] if 'notas' in turno_data else None
                )
                # Agregamos información relacionada
                turno.paciente_nombre = turno_data['paciente_nombre']
                turno.usuario_nombre = turno_data['usuario_nombre']
                turnos.append(turno)
        
        # Debug
        print(f"Próximos turnos encontrados: {len(turnos)}")
        
        return turnos


class Configuracion:
    def __init__(self, id_config=None, id_usuario=None, horario_inicio=None, 
                 horario_fin=None, duracion_turno=30):
        self.id_config = id_config
        self.id_usuario = id_usuario
        self.horario_inicio = horario_inicio
        self.horario_fin = horario_fin
        self.duracion_turno = duracion_turno
        self.db = DatabaseConnection()
    
    def guardar(self):
        """Guarda o actualiza una configuración en la base de datos."""
        if self.id_config:
            # Actualizar configuración existente
            query = """
                UPDATE configuraciones 
                SET id_usuario = %s, horario_inicio = %s, horario_fin = %s, duracion_turno = %s 
                WHERE id_config = %s
            """
            params = (
                self.id_usuario, self.horario_inicio, self.horario_fin, 
                self.duracion_turno, self.id_config
            )
            return self.db.execute_query(query, params)
        else:
            # Verificar si ya existe configuración para este usuario
            query = "SELECT id_config FROM configuraciones WHERE id_usuario = %s"
            result = self.db.execute_query(query, (self.id_usuario,))
            
            if result and isinstance(result, list) and len(result) > 0:
                # Actualizar la configuración existente
                self.id_config = result[0]['id_config']
                return self.guardar()
            else:
                # Insertar nueva configuración
                query = """
                    INSERT INTO configuraciones 
                    (id_usuario, horario_inicio, horario_fin, duracion_turno) 
                    VALUES (%s, %s, %s, %s)
                """
                params = (
                    self.id_usuario, self.horario_inicio, self.horario_fin, 
                    self.duracion_turno
                )
                result = self.db.execute_query(query, params)
                if result:
                    self.id_config = result
                return result
    
    @classmethod
    def obtener_por_usuario(cls, id_usuario):
        """Obtiene la configuración de un usuario específico."""
        db = DatabaseConnection()
        query = "SELECT * FROM configuraciones WHERE id_usuario = %s"
        result = db.execute_query(query, (id_usuario,))
        
        if result and isinstance(result, list) and len(result) > 0:
            config_data = result[0]
            return cls(
                id_config=config_data['id_config'],
                id_usuario=config_data['id_usuario'],
                horario_inicio=config_data['horario_inicio'],
                horario_fin=config_data['horario_fin'],
                duracion_turno=config_data['duracion_turno']
            )
        # Si no existe, retornamos una configuración por defecto
        return cls(id_usuario=id_usuario)