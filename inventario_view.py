# inventario_view.py
import flet as ft
from typing import List, Dict, Any
import threading
import time
import requests

def crear_vista_inventario(inventory_service, on_update_ui, page):
    # Campo para mostrar alerta de bajo umbral
    alerta_umbral = ft.Container(expand=False) # Contenedor para la alerta

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

    # Variable para rastrear si hay un campo de cantidad en edición
    # Ahora es parte de la 'vista' y se puede acceder desde fuera
    campo_en_edicion_id = None

    # FUNCIÓN PARA VERIFICAR ALERTAS PERIÓDICAMENTE
    def verificar_alertas_periodicamente():
        while True:
            try:
                items = inventory_service.obtener_inventario()
                
                # VERIFICAR ALERTAS DE INGREDIENTES BAJOS
                umbral_bajo = 5 # UMBRAL PARA AVISAR (PUEDES CAMBIAR ESTE VALOR)
                ingredientes_bajos = [item for item in items if item['cantidad_disponible'] <= umbral_bajo]

                # ACTUALIZAR CONTENIDO DE ALERTA
                if ingredientes_bajos:
                    nombres_bajos = ", ".join([item['nombre'] for item in ingredientes_bajos])
                    alerta_umbral.content = ft.Row([
                        ft.Icon(ft.Icons.WARNING, color=ft.Colors.WHITE),
                        ft.Text(f"⚠️ Alerta de Inventario: {nombres_bajos} están por debajo del umbral ({umbral_bajo})", color=ft.Colors.WHITE)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    alerta_umbral.bgcolor = ft.Colors.RED_700
                    alerta_umbral.padding = 10
                    alerta_umbral.border_radius = 5
                    alerta_umbral.visible = True
                else:
                    alerta_umbral.visible = False # Ocultar si no hay alertas
                # --- FIN VERIFICACIÓN ---
                
            except Exception as e:
                print(f"Error en verificación periódica: {e}")
                time.sleep(30) # ESPERAR 30 SEGUNDOS ANTES DE REINTENTAR

    # INICIAR VERIFICACIÓN PERIÓDICA EN UN HILO SEPARADO
    hilo_verificacion = threading.Thread(target=verificar_alertas_periodicamente, daemon=True)
    hilo_verificacion.start()

    def actualizar_lista():
        nonlocal campo_en_edicion_id # Acceder a la variable del scope superior
        # Si hay un campo en edición, NO actualizar la lista para no perder el foco/valor
        if campo_en_edicion_id is not None:
            print(f"No se actualiza la lista de inventario porque el campo {campo_en_edicion_id} está en edición.")
            return # Salir sin hacer nada

        print("Actualizando lista de inventario...") # Mensaje de depuración
        try:
            items = inventory_service.obtener_inventario()
            
            # --- VERIFICAR ALERTAS DE INGREDIENTES BAJOS ---
            umbral_bajo = 5 # UMBRAL PARA AVISAR (PUEDES CAMBIAR ESTE VALOR)
            ingredientes_bajos = [item for item in items if item['cantidad_disponible'] <= umbral_bajo]

            # ACTUALIZAR CONTENIDO DE ALERTA
            if ingredientes_bajos:
                nombres_bajos = ", ".join([item['nombre'] for item in ingredientes_bajos])
                alerta_umbral.content = ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.WHITE),
                    ft.Text(f"⚠️ Alerta de Inventario: {nombres_bajos} están por debajo del umbral ({umbral_bajo})", color=ft.Colors.WHITE)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                alerta_umbral.bgcolor = ft.Colors.RED_700
                alerta_umbral.padding = 10
                alerta_umbral.border_radius = 5
                alerta_umbral.visible = True
            else:
                alerta_umbral.visible = False # Ocultar si no hay alertas
            # --- FIN VERIFICACIÓN ---
            
            # Limpiar la lista visual antes de reconstruir
            lista_inventario.controls.clear()

            for item in items:
                item_id = item['id']
                # Campo de texto para ingresar la nueva cantidad
                nuevo_cantidad_input = ft.TextField(
                    label="Nueva Cantidad",
                    value=str(item['cantidad_disponible']), # Valor inicial es la cantidad actual
                    width=120,
                    input_filter=ft.NumbersOnlyInputFilter(),
                    hint_text=f"Actual: {item['cantidad_disponible']}",
                    data=item_id # Almacenar ID para identificarlo
                )

                # Función para manejar el foco (inicio de edición)
                def on_focus_cantidad(e, item_id=item_id):
                    nonlocal campo_en_edicion_id
                    campo_en_edicion_id = item_id
                    print(f"Campo {item_id} en edición.")

                # Función para manejar la pérdida de foco (fin de edición)
                def on_blur_cantidad(e, item_id=item_id):
                    nonlocal campo_en_edicion_id
                    if campo_en_edicion_id == item_id:
                        campo_en_edicion_id = None
                        print(f"Campo {item_id} dejó de estar en edición.")
                        # Opcional: Forzar actualización de la lista después de salir del campo
                        # Esto puede ser útil si quieres que el valor del campo se actualice inmediatamente
                        # al salir del campo, incluso si no se presiona "Actualizar".
                        # on_update_ui() # Descomentar si se desea este comportamiento

                # Asignar las funciones de foco
                nuevo_cantidad_input.on_focus = lambda e, id=item_id: on_focus_cantidad(e, id)
                nuevo_cantidad_input.on_blur = lambda e, id=item_id: on_blur_cantidad(e, id)

                # Botón Actualizar
                boton_actualizar = ft.ElevatedButton(
                    text="Actualizar",
                    on_click=lambda e, id=item_id, input_cantidad=nuevo_cantidad_input, unidad_original=item['unidad_medida']: actualizar_ingrediente(id, input_cantidad, unidad_original),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
                )

                # Botón Eliminar
                boton_eliminar = ft.ElevatedButton(
                    text="Eliminar",
                    on_click=lambda e, id=item_id: eliminar_item_click(id),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                )

                # No se crea ningún campo de texto ni botón para editar cantidad
                # Solo se muestran los datos del ítem, el campo de texto para la nueva cantidad y los botones de eliminar y actualizar
                item_row = ft.Container(
                    content=ft.Column([
                        ft.Text(f"{item['nombre']}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Cantidad: {item['cantidad_disponible']} {item['unidad_medida']}", size=14),
                        ft.Text(f"Registrado: {item['fecha_registro']}", size=12, color=ft.Colors.GREY_500),
                        ft.Row([
                            nuevo_cantidad_input, # Campo de texto para nueva cantidad
                            boton_actualizar,      # Botón Actualizar
                            boton_eliminar         # Botón Eliminar
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
            alerta_umbral.visible = False # Asegurar que no se muestre alerta si hay error al cargar
            page.update()

    # --- FUNCIÓN: actualizar_ingrediente ---
    # Actualiza la cantidad de un ingrediente específico.
    def actualizar_ingrediente(item_id: int, input_cantidad: ft.TextField, unidad_original: str):
        """Actualiza la cantidad de un ingrediente."""
        # Asegurarse de que el campo no esté en edición antes de tomar su valor
        # (esto puede no ser necesario si se maneja bien el foco)
        nonlocal campo_en_edicion_id
        if campo_en_edicion_id == item_id:
             # Opcional: Forzar la pérdida de foco antes de leer el valor
             # input_cantidad.blur() # Flet no tiene un blur() directo en el control aquí
             # Es mejor dejar que el usuario mueva el foco manualmente o use on_change
             # para capturar el valor antes de que se refresque la UI.
             # Para esta solución, asumimos que si se presiona "Actualizar",
             # el usuario ya ha terminado de escribir y movido el foco o presionado enter (si aplica).
             # Actualizamos el valor del backend con el del campo de texto.
             pass # No hacer nada especial aquí, solo leer el valor del campo

        try:
            nueva_cantidad_str = input_cantidad.value.strip()
            if not nueva_cantidad_str:
                print("Ingrese una cantidad válida.")
                return
            nueva_cantidad = int(nueva_cantidad_str)
            if nueva_cantidad < 0: # Permitir cero para "agotado"
                print("La cantidad no puede ser negativa.")
                return

            # Actualizar el ítem en el backend
            inventory_service.actualizar_item_inventario(item_id, nueva_cantidad, unidad=unidad_original)

            # Limpiar el indicador de edición si es necesario
            if campo_en_edicion_id == item_id:
                campo_en_edicion_id = None

            # Actualizar la UI general
            on_update_ui() # Esto llamará a actualizar_lista, que ahora puede verificar campo_en_edicion_id

        except ValueError:
            print("Cantidad debe ser un número entero válido.")
        except Exception as ex:
            print(f"Error al actualizar ítem: {ex}")

    def agregar_item_click(e):
        nombre = nombre_input.value
        cantidad = cantidad_input.value
        unidad = unidad_input.value

        if not nombre or not cantidad:
            return

        try:
            # Transformar el nombre: primera letra mayúscula, resto minúsculas
            nombre_formateado = nombre.strip().capitalize()
            inventory_service.agregar_item_inventario(nombre_formateado, int(cantidad), unidad)
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
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 400:
                # Mostrar mensaje de error específico del backend
                print(f"Error al eliminar ítem: {http_err.response.text}")
                # Mostrar una alerta en la interfaz de Flet
                def cerrar_alerta(e):
                    page.close(dlg_error)
                
                dlg_error = ft.AlertDialog(
                    title=ft.Text("No se puede eliminar"),
                    content=ft.Text(http_err.response.text), # Muestra el mensaje del backend
                    actions=[ft.TextButton("Aceptar", on_click=cerrar_alerta)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.dialog = dlg_error
                dlg_error.open = True
                page.update()
            else:
                # Otro error HTTP (como 500)
                print(f"Error HTTP inesperado al eliminar ítem: {http_err}")
                # Opcional: Mostrar una alerta genérica para otros errores
                def cerrar_alerta_gen(e):
                    page.close(dlg_error_gen)
                
                dlg_error_gen = ft.AlertDialog(
                    title=ft.Text("Error"),
                    content=ft.Text(f"Error inesperado al eliminar: {http_err.response.text}"),
                    actions=[ft.TextButton("Aceptar", on_click=cerrar_alerta_gen)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.dialog = dlg_error_gen
                dlg_error_gen.open = True
                page.update()
        except Exception as ex:
            print(f"Error inesperado al eliminar ítem: {ex}")
            # Opcional: Mostrar una alerta para errores no HTTP
            def cerrar_alerta_ex(e):
                page.close(dlg_error_ex)
            
            dlg_error_ex = ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text(f"Error inesperado: {str(ex)}"),
                actions=[ft.TextButton("Aceptar", on_click=cerrar_alerta_ex)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.dialog = dlg_error_ex
            dlg_error_ex.open = True
            page.update()

    vista = ft.Container(
        content=ft.Column([
            alerta_umbral, # <-- AÑADIR EL CONTENEDOR DE ALERTA AL PRINCIPIO
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

    # Asignar la variable de estado y la función de actualización a la vista
    vista.campo_en_edicion_id = campo_en_edicion_id
    vista.actualizar_lista = actualizar_lista
    return vista