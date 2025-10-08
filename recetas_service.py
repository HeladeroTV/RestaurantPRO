import requests
from typing import List, Dict, Any

class RecetasService:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def obtener_recetas(self) -> List[Dict[str, Any]]:
        r = requests.get(f"{self.base_url}/recetas/")
        r.raise_for_status()
        return r.json()

    def crear_receta(self, nombre: str, descripcion: str, ingredientes: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "nombre": nombre,
            "descripcion": descripcion,
            "ingredientes": ingredientes
        }
        r = requests.post(f"{self.base_url}/recetas/", json=payload)
        r.raise_for_status()
        return r.json()

    def eliminar_receta(self, receta_id: int) -> Dict[str, Any]:
        r = requests.delete(f"{self.base_url}/recetas/{receta_id}")
        r.raise_for_status()
        return r.json()