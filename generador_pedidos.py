import requests
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class GeneradorPedidosAleatorios:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.menus = self._obtener_menu()

    def _obtener_menu(self) -> List[Dict[str, Any]]:
        """Obtiene el menú actual del backend."""
        try:
            r = requests.get(f"{self.base_url}/menu/items")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"❌ Error al obtener menú: {e}")
            return []

    def _generar_pedido_aleatorio(self, fecha: datetime = None) -> Dict[str, Any]:
        """Genera un pedido aleatorio."""
        if not self.menus:
            raise ValueError("❌ No hay menú disponible")

        # Seleccionar mesa aleatoria
        mesa_numero = random.choice([1, 2, 3, 4, 5, 6, 99])  # 99 = App

        # Seleccionar items aleatorios
        num_items = random.randint(1, 4)  # 1 a 4 items por pedido
        items = []
        total = 0

        for _ in range(num_items):
            item = random.choice(self.menus)
            cantidad = random.randint(1, 2)  # 1 o 2 de cada item
            items.append({
                "nombre": item["nombre"],
                "precio": item["precio"] * cantidad,
                "tipo": item["tipo"],
                "cantidad": cantidad
            })
            total += item["precio"] * cantidad

        # Estado aleatorio
        estado = random.choice(["Pendiente", "En preparacion", "Listo", "Entregado", "Pagado"])

        # Fecha
        if fecha is None:
            fecha_pedido = datetime.now()
        else:
            fecha_pedido = fecha

        return {
            "mesa_numero": mesa_numero,
            "items": items,
            "estado": estado,
            "notas": random.choice(["", "Sin cebolla", "Con salsa", "Sin sal", "Doble queso"]),
            "fecha_hora": fecha_pedido.strftime("%Y-%m-%d %H:%M:%S")
        }

    def generar_pedidos_por_meses(self, meses_atras: int = 3, pedidos_por_mes: int = 20):
        """Genera pedidos distribuidos en diferentes meses."""
        if not self.menus:
            print("❌ No se puede generar pedidos: no hay menú disponible")
            return

        for mes_atras in range(meses_atras):
            # Calcular el mes objetivo
            mes_fecha = datetime.now() - timedelta(days=mes_atras * 30)
            
            # Obtener el primer y último día del mes
            primer_dia = mes_fecha.replace(day=1)
            if mes_fecha.month == 12:
                ultimo_dia = primer_dia.replace(year=mes_fecha.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                ultimo_dia = primer_dia.replace(month=mes_fecha.month + 1) - timedelta(days=1)

            print(f"📅 Generando {pedidos_por_mes} pedidos para {primer_dia.strftime('%Y-%m')}...")

            for i in range(pedidos_por_mes):
                # Fecha aleatoria dentro del mes
                dias_en_mes = (ultimo_dia - primer_dia).days
                dias_aleatorios = random.randint(0, dias_en_mes)
                fecha_pedido = primer_dia + timedelta(days=dias_aleatorios)

                pedido = self._generar_pedido_aleatorio(fecha_pedido)

                try:
                    # Crear pedido en el backend
                    r = requests.post(f"{self.base_url}/pedidos", json=pedido)
                    r.raise_for_status()
                    
                    total_pedido = sum(item['precio'] for item in pedido['items'])
                    print(f"   ✅ Pedido {i+1}/{pedidos_por_mes}: Mesa {pedido['mesa_numero']}, ${total_pedido:.2f}, {pedido['fecha_hora']}")
                except requests.exceptions.HTTPError as e:
                    print(f"   ❌ Error HTTP: {e}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

        print(f"✅ Se crearon {meses_atras * pedidos_por_mes} pedidos distribuidos en {meses_atras} meses")

    def generar_pedidos_por_semanas(self, semanas_atras: int = 4, pedidos_por_semana: int = 15):
        """Genera pedidos distribuidos en diferentes semanas."""
        if not self.menus:
            print("❌ No se puede generar pedidos: no hay menú disponible")
            return

        for semana_atras in range(semanas_atras):
            # Calcular la semana objetivo (lunes de esa semana)
            hoy = datetime.now()
            dias_atras = semana_atras * 7
            lunes_semana = (hoy - timedelta(days=dias_atras)).replace(hour=0, minute=0, second=0, microsecond=0)
            lunes_semana = lunes_semana - timedelta(days=lunes_semana.weekday())  # Ajustar a lunes

            print(f"📅 Generando {pedidos_por_semana} pedidos para la semana del {lunes_semana.strftime('%Y-%m-%d')}...")

            for i in range(pedidos_por_semana):
                # Fecha aleatoria dentro de la semana (lunes a domingo)
                dias_aleatorios = random.randint(0, 6)
                hora_aleatoria = random.randint(10, 22)  # Entre las 10 AM y 10 PM
                fecha_pedido = lunes_semana + timedelta(days=dias_aleatorios, hours=hora_aleatoria)

                pedido = self._generar_pedido_aleatorio(fecha_pedido)

                try:
                    # Crear pedido en el backend
                    r = requests.post(f"{self.base_url}/pedidos", json=pedido)
                    r.raise_for_status()
                    
                    total_pedido = sum(item['precio'] for item in pedido['items'])
                    print(f"   ✅ Pedido {i+1}/{pedidos_por_semana}: Mesa {pedido['mesa_numero']}, ${total_pedido:.2f}, {pedido['fecha_hora']}")
                except requests.exceptions.HTTPError as e:
                    print(f"   ❌ Error HTTP: {e}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

        print(f"✅ Se crearon {semanas_atras * pedidos_por_semana} pedidos distribuidos en {semanas_atras} semanas")

    def generar_pedidos_distribuidos(self, total_pedidos: int, rango_dias: int = 90):
        """Genera pedidos distribuidos aleatoriamente en un rango de días."""
        if not self.menus:
            print("❌ No se puede generar pedidos: no hay menú disponible")
            return

        print(f"📅 Generando {total_pedidos} pedidos distribuidos en {rango_dias} días...")

        for i in range(total_pedidos):
            # Fecha aleatoria dentro del rango
            dias_aleatorios = random.randint(0, rango_dias)
            hora_aleatoria = random.randint(10, 22)  # Entre las 10 AM y 10 PM
            fecha_pedido = datetime.now() - timedelta(days=dias_aleatorios, hours=hora_aleatoria)

            pedido = self._generar_pedido_aleatorio(fecha_pedido)

            try:
                # Crear pedido en el backend
                r = requests.post(f"{self.base_url}/pedidos", json=pedido)
                r.raise_for_status()
                
                total_pedido = sum(item['precio'] for item in pedido['items'])
                print(f"✅ Pedido {i+1}/{total_pedidos}: Mesa {pedido['mesa_numero']}, ${total_pedido:.2f}, {pedido['fecha_hora']}")
            except requests.exceptions.HTTPError as e:
                print(f"❌ Error HTTP al crear pedido {i+1}: {e}")
            except Exception as e:
                print(f"❌ Error desconocido al crear pedido {i+1}: {e}")

        print(f"✅ Se crearon {total_pedidos} pedidos distribuidos")

# Ejemplo de uso
if __name__ == "__main__":
    generador = GeneradorPedidosAleatorios()

    print("Seleccione una opción:")
    print("1. Generar pedidos distribuidos en meses (últimos 3 meses, 20 por mes)")
    print("2. Generar pedidos distribuidos en semanas (últimas 4 semanas, 15 por semana)")
    print("3. Generar pedidos distribuidos aleatoriamente (100 pedidos en 90 días)")

    opcion = input("Ingrese opción (1-3): ")

    if opcion == "1":
        generador.generar_pedidos_por_meses(meses_atras=3, pedidos_por_mes=20)
    elif opcion == "2":
        generador.generar_pedidos_por_semanas(semanas_atras=4, pedidos_por_semana=15)
    elif opcion == "3":
        generador.generar_pedidos_distribuidos(total_pedidos=100, rango_dias=90)
    else:
        print("❌ Opción no válida")