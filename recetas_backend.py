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

class RecetaCreate(BaseModel):
    nombre: str
    descripcion: str = ""

class IngredienteReceta(BaseModel):
    ingrediente_id: int
    cantidad_necesaria: int
    unidad: str = "unidad"

class RecetaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str
    ingredientes: List[dict]

# NUEVA SUB-APP PARA RECETAS
recetas_app = FastAPI(title="Recetas API")

@recetas_app.get("/", response_model=List[RecetaResponse])
def obtener_recetas(conn = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT r.id, r.nombre, r.descripcion
            FROM recetas r
            ORDER BY r.nombre
        """)
        recetas = []
        for row in cursor.fetchall():
            cursor.execute("""
                SELECT ir.ingrediente_id, i.nombre, ir.cantidad_necesaria, ir.unidad
                FROM ingredientes_recetas ir
                JOIN inventario i ON i.id = ir.ingrediente_id
                WHERE ir.receta_id = %s
            """, (row['id'],))
            ingredientes = [
                {
                    "ingrediente_id": r['ingrediente_id'],
                    "nombre": r['nombre'],
                    "cantidad_necesaria": r['cantidad_necesaria'],
                    "unidad": r['unidad']
                }
                for r in cursor.fetchall()
            ]
            recetas.append({
                "id": row['id'],
                "nombre": row['nombre'],
                "descripcion": row['descripcion'],
                "ingredientes": ingredientes
            })
        return recetas

@recetas_app.post("/", response_model=RecetaResponse)
def crear_receta(receta: RecetaCreate, ingredientes: List[IngredienteReceta], conn = Depends(get_db)):
    with conn.cursor() as cursor:
        # Crear receta
        cursor.execute("""
            INSERT INTO recetas (nombre, descripcion)
            VALUES (%s, %s)
            RETURNING id
        """, (receta.nombre, receta.descripcion))
        receta_id = cursor.fetchone()['id']

        # Agregar ingredientes
        for ing in ingredientes:
            cursor.execute("""
                INSERT INTO ingredientes_recetas (receta_id, ingrediente_id, cantidad_necesaria, unidad)
                VALUES (%s, %s, %s, %s)
            """, (receta_id, ing.ingrediente_id, ing.cantidad_necesaria, ing.unidad))

        conn.commit()

        return obtener_receta_por_id(receta_id, conn)

def obtener_receta_por_id(receta_id: int, conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT r.id, r.nombre, r.descripcion
            FROM recetas r
            WHERE r.id = %s
        """, (receta_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Receta no encontrada")

        cursor.execute("""
            SELECT ir.ingrediente_id, i.nombre, ir.cantidad_necesaria, ir.unidad
            FROM ingredientes_recetas ir
            JOIN inventario i ON i.id = ir.ingrediente_id
            WHERE ir.receta_id = %s
        """, (receta_id,))
        ingredientes = [
            {
                "ingrediente_id": r['ingrediente_id'],
                "nombre": r['nombre'],
                "cantidad_necesaria": r['cantidad_necesaria'],
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

@recetas_app.delete("/{receta_id}")
def eliminar_receta(receta_id: int, conn = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM ingredientes_recetas WHERE receta_id = %s", (receta_id,))
        cursor.execute("DELETE FROM recetas WHERE id = %s", (receta_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Receta no encontrada")
        conn.commit()
        return {"status": "ok", "message": "Receta eliminada"}