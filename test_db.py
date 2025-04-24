# test_db.py
from db_conexion import db

def test_db_connection():
    try:
        # Obtener conexión
        connection = db.get_connection()
        
        if connection and connection.is_connected():
            print("Conexión exitosa a la base de datos")
            
            # Probar una consulta simple
            result = db.execute_query("SELECT * FROM pacientes LIMIT 5")
            
            if result:
                print(f"Consulta exitosa. Número de pacientes: {len(result)}")
                for paciente in result:
                    print(f"ID: {paciente['id']}, Nombre: {paciente['nombre']} {paciente['apellido']}")
            else:
                print("La consulta no devolvió resultados.")
            
            return True
    except Exception as e:
        print(f"Error al probar la conexión: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()