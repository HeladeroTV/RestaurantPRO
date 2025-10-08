# === INVENTARIO_SERVICE.PY ===
# Cliente HTTP para interactuar con la API de inventario del sistema de restaurante.

import requests
from typing import List, Dict, Any

class InventoryService:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    # === MÉTODO: obtener_inventario ===
    # Obtiene la lista completa de items en inventario desde el backend.

    def obtener_inventario(self) -> List[Dict[str, Any]]:
        r = requests.get(f"{self.base_url}/inventario")
        r.raise_for_status()
        return r.json()

    # === MÉTODO: agregar_item_inventario ===
    # Agrega un nuevo ítem al inventario en el backend.

    def agregar_item_inventario(self, nombre: str, cantidad: int, unidad: str = "unidad") -> Dict[str, Any]:
        payload = {
            "nombre": nombre,
            "cantidad_disponible": cantidad,
            "unidad_medida": unidad
        }
        r = requests.post(f"{self.base_url}/inventario", json=payload)
        r.raise_for_status()
        return r.json()

    # === MÉTODO: actualizar_item_inventario ===
    # Actualiza la cantidad y unidad de un ítem existente en el inventario.

    def actualizar_item_inventario(self, item_id: int, cantidad: int, unidad: str = "unidad") -> Dict[str, Any]:
        payload = {
            "cantidad_disponible": cantidad,
            "unidad_medida": unidad
        }
        r = requests.put(f"{self.base_url}/inventario/{item_id}", json=payload)
        r.raise_for_status()
        return r.json()

    # === MÉTODO: eliminar_item_inventario ===
    # Elimina un ítem del inventario en el backend.

    def eliminar_item_inventario(self, item_id: int) -> Dict[str, Any]:
        r = requests.delete(f"{self.base_url}/inventario/{item_id}")
        r.raise_for_status()
        return r.json()