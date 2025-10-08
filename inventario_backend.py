from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "dbname=restaurant_db user=postgres password=postgres host=localhost port=5432"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

class InventarioItem(BaseModel):
    nombre: str
    cantidad_disponible: int
    unidad_medida: str = "unidad"

class InventarioUpdate(BaseModel):
    cantidad_disponible: int
    unidad_medida: str = "unidad"

class InventarioResponse(BaseModel):
    id: int
    nombre: str
    cantidad_disponible: int
    unidad_medida: str
    fecha_registro: str
    fecha_actualizacion: str

# NUEVA API PARA INVENTARIO
inventario_app = FastAPI(title="Inventory API")

# CORREGIDO: Cambié "/inventario" por "/" para que al montar en /inventario, sea /inventario/
@inventario_app.get("/", response_model=List[InventarioResponse])
def obtener_inventario(conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, nombre, cantidad_disponible, unidad_medida, fecha_registro, fecha_actualizacion
            FROM inventario
            ORDER BY nombre
        """)
        items = []
        for row in cursor.fetchall():
            items.append({
                "id": row['id'],
                "nombre": row['nombre'],
                "cantidad_disponible": row['cantidad_disponible'],
                "unidad_medida": row['unidad_medida'],
                "fecha_registro": str(row['fecha_registro']),
                "fecha_actualizacion": str(row['fecha_actualizacion'])
            })
        return items

@inventario_app.post("/", response_model=InventarioResponse)
def agregar_item_inventario(item: InventarioItem, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO inventario (nombre, cantidad_disponible, unidad_medida)
            VALUES (%s, %s, %s)
            RETURNING id, nombre, cantidad_disponible, unidad_medida, fecha_registro, fecha_actualizacion
        """, (item.nombre, item.cantidad_disponible, item.unidad_medida))
        result = cursor.fetchone()
        conn.commit()
        return {
            "id": result['id'],
            "nombre": result['nombre'],
            "cantidad_disponible": result['cantidad_disponible'],
            "unidad_medida": result['unidad_medida'],
            "fecha_registro": str(result['fecha_registro']),
            "fecha_actualizacion": str(result['fecha_actualizacion'])
        }

@inventario_app.put("/{item_id}", response_model=InventarioResponse)
def actualizar_item_inventario(item_id: int, update_data: InventarioUpdate, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE inventario
            SET cantidad_disponible = %s, unidad_medida = %s, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, nombre, cantidad_disponible, unidad_medida, fecha_registro, fecha_actualizacion
        """, (update_data.cantidad_disponible, update_data.unidad_medida, item_id))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Ítem no encontrado")
        conn.commit()
        return {
            "id": result['id'],
            "nombre": result['nombre'],
            "cantidad_disponible": result['cantidad_disponible'],
            "unidad_medida": result['unidad_medida'],
            "fecha_registro": str(result['fecha_registro']),
            "fecha_actualizacion": str(result['fecha_actualizacion'])
        }

@inventario_app.delete("/{item_id}")
def eliminar_item_inventario(item_id: int, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM inventario WHERE id = %s", (item_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ítem no encontrado")
        conn.commit()
        return {"status": "ok"}