import mysql.connector
from mysql.connector import Error
import os
from flask import current_app

class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.connection = None
            cls._instance.initialize_connection()
        return cls._instance
    
    def initialize_connection(self):
        """Inicializa la conexión a la base de datos."""
        try:
            # Configuración para XAMPP
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',  # Usuario por defecto en XAMPP
                password='',  # Sin contraseña por defecto en XAMPP
                database='web_turnos'
            )
            
            if self.connection.is_connected():
                print("Conexión a la base de datos establecida exitosamente")
        except Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            self.connection = None
    
    def get_connection(self):
        """Retorna la conexión a la base de datos."""
        # Si la conexión es None o no está conectada, intentamos reconectar
        if self.connection is None or not self.connection.is_connected():
            print("Conexión no disponible. Intentando reconectar...")
            self.initialize_connection()
            
        # Verificar después de intentar reconectar
        if self.connection is None:
            raise Exception("No se pudo establecer conexión con la base de datos.")
            
        return self.connection
    
    def close_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión a la base de datos cerrada")
    
    def execute_query(self, query, params=None):
        """Ejecuta una consulta SQL y retorna el resultado."""
        connection = self.get_connection()
        cursor = None
        
        try:
            cursor = connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def execute_update(self, query, params=None):
        """Ejecuta una consulta SQL de tipo INSERT, UPDATE, DELETE."""
        connection = self.get_connection()
        cursor = None
        
        try:
            cursor = connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            connection.commit()
            return cursor.lastrowid
        except Error as e:
            connection.rollback()
            print(f"Error al ejecutar la actualización: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

# Crear una instancia global de la conexión a la base de datos
db = DatabaseConnection()