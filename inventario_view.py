import flet as ft
from typing import List, Dict, Any
import threading
import time

def crear_vista_inventario(inventory_service, on_update_ui, page):
    # Campos de entrada
    nombre_input = ft.TextField(label="Nombre del producto", width=300)
    cantidad_input = ft.TextField(
        label="Cantidad disponible",
        width=300,
        input_filter=ft.NumbersOnlyInputFilter()
    )
    unidad_input = ft.TextField(label="Unidad (ej: kg, unidad, litro)", value="unidad", width=300)

    # Lista de inventario
    lista_inventario = ft.ListView(
        expand=1,
        spacing=10,
        padding=20,
        auto_scroll=True,
    )

    # FUNCIÓN PARA VERIFICAR ALERTAS PERIÓDICAMENTE
    def verificar_alertas_periodicamente():
        while True:
            try:
                items = inventory_service.obtener_inventario()
                
                # VERIFICAR ALERTAS DE INGREDIENTES BAJOS
                umbral_bajo = 5 # UMBRAL PARA AVISAR (PUEDES CAMBIAR ESTE VALOR)
                ingredientes_bajos = [item for item in items if item['cantidad_disponible'] <= umbral_bajo]

                # MOSTRAR ALERTA SI HAY INGREDIENTES BAJOS
                if ingredientes_bajos:
                    nombres_bajos = ", ".join([item['nombre'] for item in ingredientes_bajos])
                    
                    # MOSTRAR VENTANA MODAL DE ALERTA
                    def cerrar_alerta(e):
                        page.close(dlg_alerta)
                    
                    dlg_alerta = ft.AlertDialog(
                        title=ft.Text("⚠️ Alerta de Inventario"),
                        content=ft.Text(f"Los siguientes ingredientes están por debajo del umbral:\n\n{nombres_bajos}\n\nCantidad mínima: {umbral_bajo}"),
                        actions=[
                            ft.TextButton("Aceptar", on_click=cerrar_alerta)
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                    )
                    
                    # MOSTRAR ALERTA EN EL HILO PRINCIPAL
                    def mostrar_alerta():
                        page.dialog = dlg_alerta
                        dlg_alerta.open = True
                        page.update()
                    
                    page.run_thread(mostrar_alerta)
                
                time.sleep(30) # VERIFICAR CADA 30 SEGUNDOS
            except Exception as e:
                print(f"Error en verificación periódica: {e}")
                time.sleep(30) # ESPERAR 30 SEGUNDOS ANTES DE REINTENTAR

    # INICIAR VERIFICACIÓN PERIÓDICA EN UN HILO SEPARADO
    hilo_verificacion = threading.Thread(target=verificar_alertas_periodicamente, daemon=True)
    hilo_verificacion.start()

    def actualizar_lista():
        try:
            items = inventory_service.obtener_inventario()
            lista_inventario.controls.clear()

            for item in items:
                # No se crea ningún campo de texto ni botón para editar cantidad
                # Solo se muestran los datos del ítem y el botón de eliminar
                item_row = ft.Container(
                    content=ft.Column([
                        ft.Text(f"{item['nombre']}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Cantidad: {item['cantidad_disponible']} {item['unidad_medida']}", size=14),
                        ft.Text(f"Registrado: {item['fecha_registro']}", size=12, color=ft.Colors.GREY_500),
                        ft.Row([
                            # Botón Eliminar
                            ft.ElevatedButton(
                                "Eliminar",
                                on_click=lambda e, id=item['id']: eliminar_item_click(id),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                            )
                        ])
                    ]),
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    padding=10,
                    border_radius=10
                )
                lista_inventario.controls.append(item_row)
            page.update()
        except Exception as e:
            print(f"Error al cargar inventario: {e}")

    def agregar_item_click(e):
        nombre = nombre_input.value
        cantidad = cantidad_input.value
        unidad = unidad_input.value

        if not nombre or not cantidad:
            return

        try:
            inventory_service.agregar_item_inventario(nombre, int(cantidad), unidad)
            nombre_input.value = ""
            cantidad_input.value = ""
            unidad_input.value = "unidad"
            on_update_ui() # Actualiza toda la UI, incluyendo inventario
        except Exception as ex:
            print(f"Error al agregar ítem: {ex}")

    def eliminar_item_click(item_id: int):
        try:
            inventory_service.eliminar_item_inventario(item_id)
            on_update_ui() # Actualiza toda la UI, incluyendo inventario
        except Exception as ex:
            print(f"Error al eliminar ítem: {ex}")

    vista = ft.Container(
        content=ft.Column([
            ft.Divider(),
            ft.Text("Agregar nuevo ítem", size=18, weight=ft.FontWeight.BOLD),
            nombre_input,
            cantidad_input,
            unidad_input,
            ft.ElevatedButton(
                "Agregar ítem",
                on_click=agregar_item_click,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            ),
            ft.Divider(),
            ft.Text("Inventario actual", size=18, weight=ft.FontWeight.BOLD),
            lista_inventario
        ]),
        padding=20,
        expand=True
    )

    vista.actualizar_lista = actualizar_lista
    return vista