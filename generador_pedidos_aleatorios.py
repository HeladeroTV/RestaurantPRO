import psycopg2
from psycopg2.extras import RealDictCursor
import random
from datetime import datetime, timedelta
import json

class PedidoAleatorioGenerator:
    def __init__(self, database_url: str = "dbname=restaurant_db user=postgres password=postgres host=localhost port=5432"):
        """
        Inicializa el generador con la conexión a la base de datos.

        Args:
            database_url (str): Cadena de conexión a la base de datos PostgreSQL.
        """
        self.database_url = database_url
        self.mesas_validas = [1, 2, 3, 4, 5, 6, 99] # Mesas físicas y virtual

    def _obtener_menu_desde_db(self, conn):
        """Obtiene el menú actual de la base de datos."""
        with conn.cursor() as cursor:
            cursor.execute("SELECT nombre, precio FROM menu;")
            menu = cursor.fetchall()
        return menu

    def _generar_items_pedido(self, menu, num_items_min: int = 1, num_items_max: int = 5):
        """Genera una lista aleatoria de ítems para un pedido."""
        num_items = random.randint(num_items_min, num_items_max)
        items = []
        for _ in range(num_items):
            item_seleccionado = random.choice(menu)
            items.append({
                "nombre": item_seleccionado["nombre"],
                "precio": float(item_seleccionado["precio"]) # Asegurar tipo float
            })
        return items

    def _generar_fecha_aleatoria(self, dias_atras: int = 30):
        """Genera una fecha aleatoria dentro de los últimos 'dias_atras' días."""
        dias = random.randint(0, dias_atras)
        fecha_base = datetime.now() - timedelta(days=dias)
        # Generar una hora aleatoria del día
        hora = random.randint(0, 23)
        minuto = random.randint(0, 59)
        segundo = random.randint(0, 59)
        return fecha_base.replace(hour=hora, minute=minuto, second=segundo)

    def generar_pedido(self, conn, mesa_numero: int, estado: str, fecha_hora: datetime):
        """Genera un diccionario de pedido con formato compatible con la base de datos."""
        menu = self._obtener_menu_desde_db(conn)
        items = self._generar_items_pedido(menu)
        total = sum(item["precio"] for item in items)
        numero_app = random.randint(100, 999) if mesa_numero == 99 else None
        notas_posibles = ["Sin cebolla", "Poco picante", "Urgente", "Para llevar", "En la puerta", "Sin salsa"]
        notas = random.choice(notas_posibles) if random.random() > 0.7 else "" # 30% de probabilidad de nota

        return {
            "mesa_numero": mesa_numero,
            "cliente_id": None, # Puede ser NULL
            "estado": estado,
            "fecha_hora": fecha_hora,
            "items": json.dumps(items), # Convertir lista a JSON string
            "numero_app": numero_app,
            "notas": notas
        }

    def insertar_pedido_en_db(self, conn, pedido_data: dict):
        """Inserta un pedido generado en la base de datos."""
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pedidos (mesa_numero, cliente_id, estado, fecha_hora, items, numero_app, notas)
                VALUES (%(mesa_numero)s, %(cliente_id)s, %(estado)s, %(fecha_hora)s, %(items)s, %(numero_app)s, %(notas)s);
            """, pedido_data)
        conn.commit()

    def generar_y_insertar_pedidos(self, cantidad: int, dias_atras: int = 30):
        """
        Genera y almacena una cantidad específica de pedidos aleatorios en la base de datos.

        Args:
            cantidad (int): Número de pedidos a generar e insertar.
            dias_atras (int): Rango de días hacia atrás para generar fechas aleatorias (por defecto 30).
        """
        try:
            conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
            print(f"Conectado a la base de datos para generar {cantidad} pedidos...")

            for i in range(cantidad):
                # Seleccionar datos aleatorios para el pedido
                mesa_numero = random.choice(self.mesas_validas)
                estado = random.choice(["Pagado", "Entregado"])
                fecha_pedido = self._generar_fecha_aleatoria(dias_atras)

                # Generar el pedido
                pedido = self.generar_pedido(conn, mesa_numero, estado, fecha_pedido)

                # Insertar en la base de datos
                self.insertar_pedido_en_db(conn, pedido)

                print(f"  - Pedido {i+1}/{cantidad} insertado: Mesa {pedido['mesa_numero']}, Fecha {pedido['fecha_hora'].strftime('%Y-%m-%d %H:%M:%S')}, Total estimado: ${sum(item['precio'] for item in json.loads(pedido['items'])):.2f}")

            conn.close()
            print(f"\n--- Generación completada: {cantidad} pedidos insertados en la base de datos. ---")
            print("--- Ahora puedes usar la vista de Reportes para probarla. ---")

        except psycopg2.Error as e:
            print(f"Error de base de datos al generar pedidos: {e}")
        except Exception as e:
            print(f"Error inesperado al generar pedidos: {e}")

# --- USO DE LA CLASE ---
if __name__ == "__main__":
    # Asegúrate de que DATABASE_URL apunte a tu base de datos correcta
    DATABASE_URL = "dbname=restaurant_db user=postgres password=postgres host=localhost port=5432" # Cambia si es necesario

    generator = PedidoAleatorioGenerator(database_url=DATABASE_URL)

    # Generar 50 pedidos aleatorios con fechas en los últimos 30 días
    generator.generar_y_insertar_pedidos(cantidad=50, dias_atras=30)

    # O generar una cantidad diferente o con un rango de fechas distinto
    # generator.generar_y_insertar_pedidos(cantidad=100, dias_atras=7) # Últimos 7 días