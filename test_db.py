import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="restaurant_db",
        user="postgres",
        password="postgres"
    )
    print("✅ Conexión exitosa a PostgreSQL")
    conn.close()
except Exception as e:
    print(f"❌ Error al conectar: {e}")