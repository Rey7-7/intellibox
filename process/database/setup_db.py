import sqlite3
import os

# Asegurar que la carpeta exista
os.makedirs('process/database', exist_ok=True)

conn = sqlite3.connect('process/database/intellibox.db')
cursor = conn.cursor()

# Tabla de Usuarios
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
''')

# Tabla de Historial de Accesos
cursor.execute('''
    CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

conn.commit()
conn.close()
print("Base de datos creada con éxito.")