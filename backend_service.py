# === BACKEND_SERVICE.PY ===
# Cliente HTTP para interactuar con la API del backend del sistema de restaurante.

import requests
from typing import List, Dict, Any

class BackendService:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    # === MÉTODO: obtener_menu ===
    # Obtiene todos los ítems del menú desde el backend.

    def obtener_menu(self) -> List[Dict[str, Any]]:
        """Obtiene todos los ítems del menú desde el backend."""
        r = requests.get(f"{self.base_url}/menu/items")
        r.raise_for_status()
        return r.json()

    # === MÉTODO: crear_pedido ===
    # Crea un nuevo pedido en el backend.

    def crear_pedido(self, mesa_numero: int, items: List[Dict[str, Any]], estado: str = "Pendiente", notas: str = "") -> Dict[str, Any]:
        """Crea un nuevo pedido en el backend."""
        payload = {
            "mesa_numero": mesa_numero,
            "items": items,
            "estado": estado,
            "notas": notas
        }
        r = requests.post(f"{self.base_url}/pedidos", json=payload)
        r.raise_for_status()
        return r.json()

    # === MÉTODO: obtener_pedidos_activos ===
    # Obtiene todos los pedidos activos desde el backend.

    def obtener_pedidos_activos(self) -> List[Dict[str, Any]]:
        """Obtiene todos los pedidos activos desde el backend."""
        r = requests.get(f"{self.base_url}/pedidos/activos")
        r.raise_for_status()
        return r.json()

    # === MÉTODO: actualizar_estado_pedido ===
    # Actualiza el estado de un pedido en el backend.

    def actualizar_estado_pedido(self, pedido_id: int, nuevo_estado: str) -> Dict[str, Any]:
        """Actualiza el estado de un pedido en el backend."""
        r = requests.patch(f"{self.base_url}/pedidos/{pedido_id}/estado", params={"estado": nuevo_estado})
        r.raise_for_status()
        return r.json()

    # === MÉTODO: obtener_mesas ===
    # Obtiene la lista de mesas desde el backend.

    def obtener_mesas(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de mesas desde el backend."""
        r = requests.get(f"{self.base_url}/mesas")
        r.raise_for_status()
        return r.json()

    # === MÉTODO: eliminar_ultimo_item ===
    # Elimina el último ítem de un pedido en el backend.

    def eliminar_ultimo_item(self, pedido_id: int) -> Dict[str, Any]:
        """
        Elimina el último ítem de un pedido en el backend.
        """
        r = requests.delete(f"{self.base_url}/pedidos/{pedido_id}/ultimo_item")
        r.raise_for_status()
        return r.json()

    # === MÉTODO: actualizar_pedido ===
    # Actualiza completamente un pedido en el backend.

    def actualizar_pedido(self, pedido_id: int, mesa_numero: int, items: List[Dict[str, Any]], estado: str = "Pendiente", notas: str = "") -> Dict[str, Any]:
        """
        Actualiza completamente un pedido en el backend.
        """
        payload = {
            "mesa_numero": mesa_numero,
            "items": items,
            "estado": estado,
            "notas": notas
        }
        r = requests.put(f"{self.base_url}/pedidos/{pedido_id}", json=payload)
        r.raise_for_status()
        return r.json()

    # === MÉTODO: eliminar_pedido ===
    # Elimina un pedido completamente del backend.

    def eliminar_pedido(self, pedido_id: int) -> Dict[str, Any]:
        """
        Elimina un pedido completamente del backend.
        """
        r = requests.delete(f"{self.base_url}/pedidos/{pedido_id}")
        r.raise_for_status()
        return r.json()

    # === MÉTODO: agregar_item_menu ===
    # Agrega un nuevo ítem al menú en el backend.

    def agregar_item_menu(self, nombre: str, precio: float, tipo: str) -> Dict[str, Any]:
        """
        Agrega un nuevo ítem al menú en el backend.
        """
        payload = {
            "nombre": nombre,
            "precio": precio,
            "tipo": tipo
        }
        r = requests.post(f"{self.base_url}/menu/items", json=payload)
        r.raise_for_status()
        return r.json()

    # === MÉTODO: eliminar_item_menu ===
    # Elimina un ítem del menú en el backend.

    def eliminar_item_menu(self, nombre: str, tipo: str) -> Dict[str, Any]:
        """
        Elimina un ítem del menú en el backend.
        """
        r = requests.delete(f"{self.base_url}/menu/items", params={"nombre": nombre, "tipo": tipo})
        r.raise_for_status()
        return r.json()

    # === MÉTODO: obtener_clientes ===
    # Obtiene la lista de clientes del backend.

    def obtener_clientes(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de clientes del backend.
        """
        r = requests.get(f"{self.base_url}/clientes")
        r.raise_for_status()
        return r.json()

    # === MÉTODO: agregar_cliente ===
    # Agrega un nuevo cliente al backend.

    def agregar_cliente(self, nombre: str, domicilio: str, celular: str) -> Dict[str, Any]:
        """
        Agrega un nuevo cliente al backend.
        """
        payload = {
            "nombre": nombre,
            "domicilio": domicilio,
            "celular": celular
        }
        r = requests.post(f"{self.base_url}/clientes", json=payload)
        r.raise_for_status()
        return r.json()

    # === MÉTODO: eliminar_cliente ===
    # Elimina un cliente del backend.

    def eliminar_cliente(self, cliente_id: int) -> Dict[str, Any]:
        """
        Elimina un cliente del backend.
        """
        r = requests.delete(f"{self.base_url}/clientes/{cliente_id}")
        r.raise_for_status()
        return r.json()