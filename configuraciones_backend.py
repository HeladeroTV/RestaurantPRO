from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "dbname=restaurant_db user=postgres password=postgres host=localhost port=5432"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

class IngredienteConfig(BaseModel):
    nombre: str
    cantidad: int
    unidad: str = "unidad"

class ConfiguracionCreate(BaseModel):  # ✅ MODELO CORREGIDO
    nombre: str
    descripcion: str = ""
    ingredientes: List[IngredienteConfig]  # ✅ AHORA ES PARTE DEL MODELO

class ConfiguracionResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str
    ingredientes: List[dict]

# NUEVA SUB-APP PARA CONFIGURACIONES
configuraciones_app = FastAPI(title="Configuraciones API")

@configuraciones_app.get("/", response_model=List[ConfiguracionResponse])
def obtener_configuraciones(conn = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT c.id, c.nombre, c.descripcion
            FROM configuraciones c
            ORDER BY c.nombre
        """)
        configs = []
        for row in cursor.fetchall():
            cursor.execute("""
                SELECT ic.ingrediente_id, i.nombre, ic.cantidad, ic.unidad
                FROM ingredientes_config ic
                JOIN inventario i ON i.id = ic.ingrediente_id
                WHERE ic.config_id = %s
            """, (row['id'],))
            ingredientes = [
                {
                    "ingrediente_id": r['ingrediente_id'],
                    "nombre": r['nombre'],
                    "cantidad": r['cantidad'],
                    "unidad": r['unidad']
                }
                for r in cursor.fetchall()
            ]
            configs.append({
                "id": row['id'],
                "nombre": row['nombre'],
                "descripcion": row['descripcion'],
                "ingredientes": ingredientes
            })
        return configs

@configuraciones_app.post("/", response_model=ConfiguracionResponse)
def crear_configuracion(config: ConfiguracionCreate, conn = Depends(get_db)):  # ✅ CAMBIOS AQUÍ
    with conn.cursor() as cursor:
        # Crear configuración
        cursor.execute("""
            INSERT INTO configuraciones (nombre, descripcion)
            VALUES (%s, %s)
            RETURNING id
        """, (config.nombre, config.descripcion))
        config_id = cursor.fetchone()['id']

        # Agregar ingredientes
        for ing in config.ingredientes:  # ✅ AHORA SE USA config.ingredientes
            # ✅ BUSCAR O CREAR POR NOMBRE
            cursor.execute("""
                SELECT id
                FROM inventario
                WHERE nombre = %s
            """, (ing.nombre,))
            ingrediente = cursor.fetchone()
            if ingrediente:
                ingrediente_id = ingrediente['id']
            else:
                # ✅ SI NO EXISTE, CREARLO EN EL INVENTARIO
                cursor.execute("""
                    INSERT INTO inventario (nombre, cantidad_disponible, unidad_medida)
                    VALUES (%s, 0, %s)
                    RETURNING id
                """, (ing.nombre, ing.unidad))
                ingrediente_id = cursor.fetchone()['id']

            cursor.execute("""
                INSERT INTO ingredientes_config (config_id, ingrediente_id, cantidad, unidad)
                VALUES (%s, %s, %s, %s)
            """, (config_id, ingrediente_id, ing.cantidad, ing.unidad))

        conn.commit()

        return obtener_config_por_id(config_id, conn)

def obtener_config_por_id(config_id: int, conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT c.id, c.nombre, c.descripcion
            FROM configuraciones c
            WHERE c.id = %s
        """, (config_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")

        cursor.execute("""
            SELECT ic.ingrediente_id, i.nombre, ic.cantidad, ic.unidad
            FROM ingredientes_config ic
            JOIN inventario i ON i.id = ic.ingrediente_id
            WHERE ic.config_id = %s
        """, (config_id,))
        ingredientes = [
            {
                "ingrediente_id": r['ingrediente_id'],
                "nombre": r['nombre'],
                "cantidad": r['cantidad'],
                "unidad": r['unidad']
            }
            for r in cursor.fetchall()
        ]
        return {
            "id": row['id'],
            "nombre": row['nombre'],
            "descripcion": row['descripcion'],
            "ingredientes": ingredientes
        }

@configuraciones_app.delete("/{config_id}")
def eliminar_configuracion(config_id: int, conn = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM ingredientes_config WHERE config_id = %s", (config_id,))
        cursor.execute("DELETE FROM configuraciones WHERE id = %s", (config_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        conn.commit()
        return {"status": "ok", "message": "Configuración eliminada"}

@configuraciones_app.post("/{config_id}/aplicar")
def aplicar_configuracion(config_id: int, conn = Depends(get_db)):
    with conn.cursor() as cursor:
        # Obtener ingredientes de la configuración
        cursor.execute("""
            SELECT ic.ingrediente_id, ic.cantidad, ic.unidad
            FROM ingredientes_config ic
            WHERE ic.config_id = %s
        """, (config_id,))
        ingredientes = cursor.fetchall()

        # Agregar ingredientes al inventario
        for ing in ingredientes:
            cursor.execute("""
                INSERT INTO inventario (nombre, cantidad_disponible, unidad_medida)
                VALUES (
                    (SELECT nombre FROM inventario WHERE id = %s),
                    %s,
                    %s
                )
                ON CONFLICT (nombre) DO UPDATE SET
                    cantidad_disponible = inventario.cantidad_disponible + %s
            """, (ing['ingrediente_id'], ing['cantidad'], ing['unidad'], ing['cantidad']))

        conn.commit()
        return {"status": "ok", "message": "Configuración aplicada"}