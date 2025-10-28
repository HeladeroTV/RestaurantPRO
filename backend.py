# === BACKEND.PY ===
# Backend API para el sistema de restaurante con integración de FastAPI y PostgreSQL.

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json





# IMPORTAR LA SUB-APP DE INVENTARIO
from inventario_backend import inventario_app
from recetas_backend import recetas_app
from configuraciones_backend import configuraciones_app
from fastapi import Query 

app = FastAPI(title="RestaurantIA Backend")

# Montar la sub-app de inventario
app.mount("/inventario", inventario_app)
app.mount("/recetas", recetas_app)
app.mount("/configuraciones", configuraciones_app)

# Configuración directa de PostgreSQL
DATABASE_URL = "dbname=restaurant_db user=postgres password=postgres host=localhost port=5432"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

# Modelos
class ItemMenu(BaseModel):
    nombre: str
    precio: float
    tipo: str

class PedidoCreate(BaseModel):
    mesa_numero: int
    items: List[dict]
    estado: str = "Pendiente"
    notas: str = ""

class PedidoResponse(BaseModel):
    id: int
    mesa_numero: int
    items: List[dict]
    estado: str
    fecha_hora: str
    numero_app: Optional[int] = None
    notas: str = ""

class ClienteCreate(BaseModel):
    nombre: str
    domicilio: str
    celular: str

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    domicilio: str
    celular: str
    fecha_registro: str

# Endpoints
@app.get("/health")
def health():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}

@app.get("/menu/items", response_model=List[ItemMenu])
def obtener_menu(conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("SELECT nombre, precio, tipo FROM menu ORDER BY tipo, nombre")
        items = cursor.fetchall()
        return items

@app.post("/pedidos", response_model=PedidoResponse)
def crear_pedido(pedido: PedidoCreate, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        numero_app = None
        if pedido.mesa_numero == 99:
            cursor.execute("SELECT MAX(numero_app) FROM pedidos WHERE mesa_numero = 99")
            max_app = cursor.fetchone()
            if max_app and max_app['max'] is not None:
                numero_app = max_app['max'] + 1
            else:
                numero_app = 1

        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO pedidos (mesa_numero, numero_app, estado, fecha_hora, items, notas)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, mesa_numero, numero_app, estado, fecha_hora, items, notas
        """, (
            pedido.mesa_numero,
            numero_app,
            pedido.estado,
            fecha_hora,
            json.dumps(pedido.items),
            pedido.notas
        ))
        
        result = cursor.fetchone()
        
        # ✅ RESTAR INGREDIENTES DE LAS RECETAS (SOLO SI TIENEN RECETA)
        for item in pedido.items:
            nombre_item = item['nombre']
            try:
                cursor.execute("""
                    SELECT r.id
                    FROM recetas r
                    WHERE r.nombre = %s
                """, (nombre_item,))
                receta = cursor.fetchone()
                if receta:
                    cursor.execute("""
                        SELECT ir.ingrediente_id, ir.cantidad_necesaria
                        FROM ingredientes_recetas ir
                        WHERE ir.receta_id = %s
                    """, (receta['id'],))
                    for ing in cursor.fetchall():
                        cursor.execute("""
                            UPDATE inventario
                            SET cantidad_disponible = cantidad_disponible - %s
                            WHERE id = %s
                        """, (ing['cantidad_necesaria'], ing['ingrediente_id']))
            except Exception:
                # ✅ SI NO EXISTE LA TABLA O HAY ERROR, CONTINUAR IGUAL
                pass
        
        conn.commit()
        # ✅ CORREGIDO: Convertir datetime a string si es necesario
        fecha_hora_str = result['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(result['fecha_hora'], datetime) else result['fecha_hora']
        
        return {
            "id": result['id'],
            "mesa_numero": result['mesa_numero'],
            "items": result['items'],
            "estado": result['estado'],
            "fecha_hora": fecha_hora_str,
            "numero_app": result['numero_app'],
            "notas": result['notas']
        }

@app.get("/pedidos/activos", response_model=List[PedidoResponse])
def obtener_pedidos_activos(conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, mesa_numero, numero_app, estado, fecha_hora, items, notas 
            FROM pedidos 
            WHERE estado IN ('Pendiente', 'En preparacion', 'Listo')
            ORDER BY fecha_hora DESC
        """)
        pedidos = []
        for row in cursor.fetchall():
            # ✅ CORREGIDO: Convertir datetime a string si es necesario
            fecha_hora_str = row['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row['fecha_hora'], datetime) else row['fecha_hora']
            pedidos.append({
                "id": row['id'],
                "mesa_numero": row['mesa_numero'],
                "numero_app": row['numero_app'],
                "estado": row['estado'],
                "fecha_hora": fecha_hora_str,
                "items": row['items'],
                "notas": row['notas']
            })
        return pedidos

@app.patch("/pedidos/{pedido_id}/estado")
def actualizar_estado_pedido(pedido_id: int, estado: str, conn: psycopg2.extensions.connection = Depends(get_db)):
    # Agregar "Pagado" a la lista de estados válidos
    if estado not in ["Pendiente", "En preparacion", "Listo", "Entregado", "Pagado"]: # <-- Añadido "Pagado"
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE pedidos SET estado = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (estado, pedido_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        conn.commit()
        return {"status": "ok"}

@app.get("/mesas")
def obtener_mesas(conn: psycopg2.extensions.connection = Depends(get_db)):
    """
    Obtiene el estado real de todas las mesas desde la base de datos.
    """
    try:
        with conn.cursor() as cursor:
            # ✅ ENFOQUE SIMPLIFICADO: Obtener mesas y verificar ocupación por separado
            mesas_result = []
            
            # Definir las mesas físicas
            mesas_fisicas = [
                {"numero": 1, "capacidad": 2},
                {"numero": 2, "capacidad": 2},
                {"numero": 3, "capacidad": 4},
                {"numero": 4, "capacidad": 4},
                {"numero": 5, "capacidad": 6},
                {"numero": 6, "capacidad": 6},
            ]
            
            for mesa in mesas_fisicas:
                # Verificar si la mesa tiene pedidos activos
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM pedidos 
                    WHERE mesa_numero = %s 
                    AND estado IN ('Pendiente', 'En preparacion', 'Listo')
                """, (mesa["numero"],))
                
                result = cursor.fetchone()
                # ✅ CORREGIDO: Asegurar que el conteo sea entero y no None
                count = result['count'] if result and result['count'] is not None else 0
                print(f"Mesa {mesa['numero']} -> COUNT: {count}")  # DEBUG
                ocupada = count > 0
                
                mesas_result.append({
                    "numero": mesa["numero"],
                    "capacidad": mesa["capacidad"],
                    "ocupada": ocupada  # ← Este valor se envía al frontend
                })
            
            # Agregar mesa virtual
            mesas_result.append({
                "numero": 99,
                "capacidad": 1,
                "ocupada": False,
                "es_virtual": True
            })
            
            return mesas_result
            
    except Exception as e:
        print(f"Error en obtener_mesas: {e}")
        # En caso de error, devolver mesas por defecto como LIBRES
        return [
            {"numero": 1, "capacidad": 2, "ocupada": False},
            {"numero": 2, "capacidad": 2, "ocupada": False},
            {"numero": 3, "capacidad": 4, "ocupada": False},
            {"numero": 4, "capacidad": 4, "ocupada": False},
            {"numero": 5, "capacidad": 6, "ocupada": False},
            {"numero": 6, "capacidad": 6, "ocupada": False},
            {"numero": 99, "capacidad": 1, "ocupada": False, "es_virtual": True}
        ]

# Endpoint para inicializar menú
@app.post("/menu/inicializar")
def inicializar_menu(conn: psycopg2.extensions.connection = Depends(get_db)):
    menu_inicial = [
        # Entradas
        ("Empanada Kunai", 70.00, "Entradas"),
        ("Dedos de queso (5pz)", 75.00, "Entradas"),
        ("Chile Relleno", 60.00, "Entradas"),
        ("Caribe Poppers", 130.00, "Entradas"),
        ("Brocheta", 50.00, "Entradas"),
        ("Rollos Primavera (2pz)", 100.00, "Entradas"),
        # Platillos
        ("Camarones roca", 160.00, "Platillos"),
        ("Teriyaki", 130.00, "Platillos"),
        ("Bonneles (300gr)", 150.00, "Platillos"),
        # Arroces
        ("Yakimeshi Especial", 150.00, "Arroces"),
        ("Yakimeshi Kunai", 140.00, "Arroces"),
        ("Yakimeshi Golden", 145.00, "Arroces"),
        ("Yakimeshi Horneado", 145.00, "Arroces"),
        ("Gohan Mixto", 125.00, "Arroces"),
        ("Gohan Crispy", 125.00, "Arroces"),
        ("Gohan Chicken", 120.00, "Arroces"),
        ("Kunai Burguer", 140.00, "Arroces"),
        ("Bomba", 105.00, "Arroces"),
        ("Bomba Especial", 135.00, "Arroces"),
        # Naturales
        ("Guamuchilito", 110.00, "Naturales"),
        ("Avocado", 125.00, "Naturales"),
        ("Grenudo Roll", 135.00, "Naturales"),
        ("Granja Roll", 115.00, "Naturales"),
        ("California Roll", 100.00, "Naturales"),
        ("California Especial", 130.00, "Naturales"),
        ("Arcoíris", 120.00, "Naturales"),
        ("Tuna Roll", 130.00, "Naturales"),
        ("Kusanagi", 130.00, "Naturales"),
        ("Kanisweet", 120.00, "Naturales"),
        # Empanizados
        ("Mar y Tierra", 95.00, "Empanizados"),
        ("Tres Quesos", 100.00, "Empanizados"),
        ("Cordon Blue", 105.00, "Empanizados"),
        ("Roka Roll", 135.00, "Empanizados"),
        ("Camarón Bacon", 110.00, "Empanizados"),
        ("Cielo, mar y tierra", 110.00, "Empanizados"),
        ("Konan Roll", 130.00, "Empanizados"),
        ("Pain Roll", 115.00, "Empanizados"),
        ("Sasori Roll", 125.00, "Empanizados"),
        ("Chikin", 130.00, "Empanizados"),
        ("Caribe Roll", 115.00, "Empanizados"),
        ("Chon", 120.00, "Empanizados"),
        # Gratinados
        ("Kunai Especial", 150.00, "Gratinados"),
        ("Chuma Roll", 145.00, "Gratinados"),
        ("Choche Roll", 140.00, "Gratinados"),
        ("Milán Roll", 135.00, "Gratinados"),
        ("Chio Roll", 145.00, "Gratinados"),
        ("Prime", 140.00, "Gratinados"),
        ("Ninja Roll", 135.00, "Gratinados"),
        ("Serranito", 135.00, "Gratinados"),
        ("Sanji", 145.00, "Gratinados"),
        ("Monkey Roll", 135.00, "Gratinados"),
        # Kunai Kids
        ("Baby Roll (8pz)", 60.00, "Kunai Kids"),
        ("Chicken Sweet (7pz)", 60.00, "Kunai Kids"),
        ("Chesse Puffs (10pz)", 55.00, "Kunai Kids"),
        # Bebidas
        ("Te refil", 35.00, "Bebidas"),
        ("Te de litro", 35.00, "Bebidas"),
        ("Coca-cola", 35.00, "Bebidas"),
        ("Agua natural", 20.00, "Bebidas"),
        ("Agua mineral", 35.00, "Bebidas"),
        # Extras
        ("Camaron", 20.00, "Extras"),
        ("Res", 15.00, "Extras"),
        ("Pollo", 15.00, "Extras"),
        ("Tocino", 15.00, "Extras"),
        ("Gratinado", 15.00, "Extras"),
        ("Aguacate", 25.00, "Extras"),
        ("Empanizado", 15.00, "Extras"),
        ("Philadelphia", 10.00, "Extras"),
        ("Tampico", 25.00, "Extras"),
        ("Siracha", 10.00, "Extras"),
        ("Soya", 10.00, "Extras"),
    ]
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM menu")
            for nombre, precio, tipo in menu_inicial:
                cursor.execute("""
                    INSERT INTO menu (nombre, precio, tipo)
                    VALUES (%s, %s, %s)
                """, (nombre, precio, tipo))
            conn.commit()
            return {"status": "ok", "items_insertados": len(menu_inicial)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al inicializar menú: {str(e)}")

# ¡NUEVO ENDPOINT! → Eliminar último ítem de un pedido
@app.delete("/pedidos/{pedido_id}/ultimo_item")
def eliminar_ultimo_item(pedido_id: int, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("SELECT items FROM pedidos WHERE id = %s", (pedido_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        items = json.loads(row['items'])
        if not items:
            raise HTTPException(status_code=400, detail="No hay ítems para eliminar")
        
        items.pop()
        cursor.execute("UPDATE pedidos SET items = %s WHERE id = %s", (json.dumps(items), pedido_id))
        conn.commit()
        return {"status": "ok"}

# ¡NUEVOS ENDPOINTS! → Gestión completa de pedidos y menú

@app.put("/pedidos/{pedido_id}")
def actualizar_pedido(pedido_id: int, pedido_actualizado: PedidoCreate, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM pedidos WHERE id = %s", (pedido_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE pedidos 
            SET mesa_numero = %s, estado = %s, fecha_hora = %s, items = %s, notas = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            pedido_actualizado.mesa_numero,
            pedido_actualizado.estado,
            fecha_hora,
            json.dumps(pedido_actualizado.items),
            pedido_actualizado.notas,
            pedido_id
        ))
        
        # ✅ RESTAR INGREDIENTES DE LAS RECETAS (SOLO SI TIENEN RECETA)
        for item in pedido_actualizado.items:
            nombre_item = item['nombre']
            cursor.execute("""
                SELECT r.id
                FROM recetas r
                WHERE r.nombre = %s
            """, (nombre_item,))
            receta = cursor.fetchone()
            if receta:
                cursor.execute("""
                    SELECT ir.ingrediente_id, ir.cantidad_necesaria
                    FROM ingredientes_recetas ir
                    WHERE ir.receta_id = %s
                """, (receta['id'],))
                for ing in cursor.fetchall():
                    cursor.execute("""
                        UPDATE inventario
                        SET cantidad_disponible = cantidad_disponible - %s
                        WHERE id = %s
                    """, (ing['cantidad_necesaria'], ing['ingrediente_id']))
        
        conn.commit()
        return {"status": "ok", "message": "Pedido actualizado"}

@app.delete("/pedidos/{pedido_id}")
def eliminar_pedido(pedido_id: int, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        conn.commit()
        return {"status": "ok", "message": "Pedido eliminado"}

@app.post("/menu/items")
def agregar_item_menu(item: ItemMenu, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO menu (nombre, precio, tipo)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (item.nombre, item.precio, item.tipo))
        item_id = cursor.fetchone()['id']
        conn.commit()
        return {"status": "ok", "id": item_id, "message": "Ítem agregado al menú"}

@app.delete("/menu/items")
def eliminar_item_menu(nombre: str, tipo: str, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM menu WHERE nombre = %s AND tipo = %s", (nombre, tipo))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ítem no encontrado en el menú")
        conn.commit()
        return {"status": "ok", "message": "Ítem eliminado del menú"}

# NUEVOS ENDPOINTS PARA GESTIÓN DE CLIENTES

@app.get("/clientes", response_model=List[ClienteResponse])
def obtener_clientes(conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, nombre, domicilio, celular, fecha_registro FROM clientes ORDER BY nombre")
        clientes = []
        for row in cursor.fetchall():
            fecha_str = row['fecha_registro'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row['fecha_registro'], datetime) else row['fecha_registro']
            clientes.append({
                "id": row['id'],
                "nombre": row['nombre'],
                "domicilio": row['domicilio'],
                "celular": row['celular'],
                "fecha_registro": fecha_str
            })
        return clientes

@app.post("/clientes", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO clientes (nombre, domicilio, celular)
            VALUES (%s, %s, %s)
            RETURNING id, nombre, domicilio, celular, fecha_registro
        """, (cliente.nombre, cliente.domicilio, cliente.celular))
        result = cursor.fetchone()
        conn.commit()
        fecha_str = result['fecha_registro'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(result['fecha_registro'], datetime) else result['fecha_registro']
        return {
            "id": result['id'],
            "nombre": result['nombre'],
            "domicilio": result['domicilio'],
            "celular": result['celular'],
            "fecha_registro": fecha_str
        }

@app.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        conn.commit()
        return {"status": "ok", "message": "Cliente eliminado"}
    
@app.get("/reportes")
def obtener_reporte(
    tipo: str,
    start_date: str,
    end_date: str,
    conn: psycopg2.extensions.connection = Depends(get_db)
):
    with conn.cursor() as cursor:
        # Consultar pedidos en el rango de fechas
        cursor.execute("""
            SELECT items, estado, fecha_hora
            FROM pedidos
            WHERE fecha_hora >= %s AND fecha_hora < %s
            AND estado IN ('Listo', 'Entregado', 'Pagado')
        """, (start_date, end_date))
        
        pedidos = cursor.fetchall()
        
        # Calcular estadísticas
        ventas_totales = 0
        pedidos_totales = len(pedidos)
        productos_vendidos = 0
        productos_mas_vendidos = {}

        for pedido in pedidos:
            # ✅ CORREGIR: El campo 'items' ya es una lista, no necesita json.loads()
            items = pedido['items']
            
            # ✅ VERIFICAR SI ES STRING Y PARSEAR SI ES NECESARIO
            if isinstance(items, str):
                items = json.loads(items)
            
            for item in items:
                nombre = item['nombre']
                precio = item['precio']
                
                ventas_totales += precio
                productos_vendidos += 1
                
                # Contar productos más vendidos
                if nombre in productos_mas_vendidos:
                    productos_mas_vendidos[nombre] += 1
                else:
                    productos_mas_vendidos[nombre] = 1

        # Ordenar productos más vendidos
        productos_mas_vendidos_lista = sorted(
            [{'nombre': k, 'cantidad': v} for k, v in productos_mas_vendidos.items()],
            key=lambda x: x['cantidad'],
            reverse=True
        )[:10]  # Top 10

        return {
            "ventas_totales": round(ventas_totales, 2),
            "pedidos_totales": pedidos_totales,
            "productos_vendidos": productos_vendidos,
            "productos_mas_vendidos": productos_mas_vendidos_lista
        }
        

@app.get("/analisis/productos")
def obtener_analisis_productos(
    start_date: str = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    conn: psycopg2.extensions.connection = Depends(get_db)
):
    """
    Obtiene el análisis de productos vendidos en un rango de fechas.
    """
    # Construir la condición de fecha si se proporcionan parámetros
    fecha_condicion = ""
    params = []
    if start_date and end_date:
        fecha_condicion = "AND fecha_hora >= %s AND fecha_hora < %s"
        params = [start_date, end_date]
    elif start_date:
        fecha_condicion = "AND fecha_hora >= %s"
        params = [start_date]
    elif end_date:
        # Si solo se da end_date, asumimos desde el principio de los tiempos hasta end_date
        fecha_condicion = "AND fecha_hora < %s"
        params = [end_date]

    with conn.cursor() as cursor:
        # Consultar ítems de pedidos en el rango de fechas y con estado de venta completada
        cursor.execute(f"""
            SELECT items
            FROM pedidos
            WHERE estado IN ('Entregado', 'Pagado') -- Ajustar según tu definición de venta completada
            {fecha_condicion}
        """, params)
        
        pedidos = cursor.fetchall()

    # Contar productos vendidos
    conteo_productos = {}
    for pedido in pedidos:
        # Asumiendo que 'items' es una lista de diccionarios
        items = pedido['items']
        if isinstance(items, str):
            items = json.loads(items) # Parsear si es string (aunque debería ser lista por el modelo de Pydantic o por cómo se inserta)

        if isinstance(items, list):
            for item in items:
                nombre = item.get('nombre')
                if nombre:
                    conteo_productos[nombre] = conteo_productos.get(nombre, 0) + 1

    # Ordenar productos
    productos_ordenados = sorted(conteo_productos.items(), key=lambda x: x[1], reverse=True)
    productos_mas_vendidos = [{"nombre": k, "cantidad": v} for k, v in productos_ordenados[:10]] # Top 10
    productos_menos_vendidos = [{"nombre": k, "cantidad": v} for k, v in productos_ordenados[-10:]] # Últimos 10 (menos vendidos)

    # Devolver el análisis
    return {
        "productos_mas_vendidos": productos_mas_vendidos,
        "productos_menos_vendidos": productos_menos_vendidos
    }


