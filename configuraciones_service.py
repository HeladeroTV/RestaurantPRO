import requests
from typing import List, Dict, Any

class ConfiguracionesService:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def obtener_configuraciones(self) -> List[Dict[str, Any]]:
        r = requests.get(f"{self.base_url}/configuraciones/")
        r.raise_for_status()
        return r.json()

    def crear_configuracion(self, nombre: str, descripcion: str, ingredientes: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "nombre": nombre,
            "descripcion": descripcion,
            "ingredientes": []  # ✅ AHORA ES PARTE DEL OBJETO PRINCIPAL
        }
        for ing in ingredientes:
            payload["ingredientes"].append({
                "nombre": ing["nombre"],
                "cantidad": ing["cantidad"],
                "unidad": ing["unidad"]
            })
        r = requests.post(f"{self.base_url}/configuraciones/", json=payload)  # ✅ ENVIAR TODO JUNTO
        r.raise_for_status()
        return r.json()

    def eliminar_configuracion(self, config_id: int) -> Dict[str, Any]:
        r = requests.delete(f"{self.base_url}/configuraciones/{config_id}")
        r.raise_for_status()
        return r.json()

    def aplicar_configuracion(self, config_id: int) -> Dict[str, Any]:
        r = requests.post(f"{self.base_url}/configuraciones/{config_id}/aplicar")
        r.raise_for_status()
        return r.json()