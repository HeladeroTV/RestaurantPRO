import flet as ft
from typing import List, Dict, Any

def crear_vista_configuraciones(config_service, inventory_service, on_update_ui, page):  # ✅ AGREGAR INVENTORY_SERVICE
    # Campos de entrada
    nombre_input = ft.TextField(label="Nombre de la configuración", width=300)
    descripcion_input = ft.TextField(label="Descripción", multiline=True, width=300)

    # Campo para nombre de ingrediente
    nombre_ingrediente_input = ft.TextField(label="Nombre del ingrediente", width=200)

    # Campo para cantidad de ingrediente
    cantidad_input = ft.TextField(
        label="Cantidad",
        width=200,
        input_filter=ft.NumbersOnlyInputFilter()
    )

    # Dropdown para unidad
    unidad_dropdown = ft.Dropdown(
        label="Unidad",
        options=[
            ft.dropdown.Option("unidad"),
            ft.dropdown.Option("kg"),
            ft.dropdown.Option("g"),
            ft.dropdown.Option("lt"),
            ft.dropdown.Option("ml"),
        ],
        value="unidad",
        width=150
    )

    # Lista de ingredientes de la configuración
    lista_ingredientes = ft.Column(spacing=5)

    # Lista de configuraciones guardadas
    lista_configuraciones_guardadas = ft.Column(spacing=10)

    def aplicar_configuracion_click(config_id: int):
        try:
            configs = config_service.obtener_configuraciones()
            config = next((c for c in configs if c["id"] == config_id), None)
            if not config:
                return

            # ✅ APLICAR INGREDIENTES AL INVENTARIO DIRECTAMENTE
            for ing in config["ingredientes"]:
                try:
                    # ✅ AGREGAR INGREDIENTE AL INVENTARIO
                    inventory_service.agregar_item_inventario(
                        nombre=ing["nombre"],
                        cantidad=ing["cantidad"],
                        unidad=ing["unidad"]
                    )
                except Exception as e:
                    print(f"Error al agregar ingrediente {ing['nombre']}: {e}")

            on_update_ui()
        except Exception as ex:
            print(f"Error al aplicar configuración: {ex}")

    def eliminar_configuracion_click(config_id: int):
        try:
            config_service.eliminar_configuracion(config_id)
            actualizar_lista_configuraciones_guardadas()  # ✅ ACTUALIZAR LISTA
            on_update_ui()
        except Exception as ex:
            print(f"Error al eliminar configuración: {ex}")

    def agregar_ingrediente_click(e):
        nombre_ing = nombre_ingrediente_input.value
        cantidad = cantidad_input.value
        unidad = unidad_dropdown.value

        if not nombre_ing or not cantidad:
            return

        item_row = ft.Container(
            content=ft.Row([
                ft.Text(f"{nombre_ing} - {cantidad} {unidad}"),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    on_click=lambda e, nombre=nombre_ing: eliminar_ingrediente_click(nombre)
                )
            ]),
            bgcolor=ft.Colors.BLUE_GREY_800,
            padding=5,
            border_radius=5
        )
        lista_ingredientes.controls.append(item_row)
        page.update()

    def eliminar_ingrediente_click(nombre_ing: str):
        # Eliminar de la lista visual
        lista_ingredientes.controls = [
            c for c in lista_ingredientes.controls
            if c.content.controls[0].value.split(" - ")[0] != nombre_ing
        ]
        page.update()

    def crear_configuracion_click(e):
        nombre = nombre_input.value
        descripcion = descripcion_input.value

        if not nombre:
            return

        # Obtener ingredientes de la lista visual
        ingredientes = []
        for control in lista_ingredientes.controls:
            texto = control.content.controls[0].value
            nombre_ing, cantidad_unidad = texto.split(" - ")
            cantidad, unidad = cantidad_unidad.split(" ", 1)
            ingredientes.append({
                "nombre": nombre_ing,  # ✅ AHORA SE USA EL NOMBRE DEL INGREDIENTE
                "cantidad": int(cantidad),
                "unidad": unidad
            })

        try:
            # ✅ MODIFICAR EL SERVICIO PARA ENVIAR NOMBRES DE INGREDIENTES
            config_service.crear_configuracion(nombre, descripcion, ingredientes)
            nombre_input.value = ""
            descripcion_input.value = ""
            nombre_ingrediente_input.value = ""
            cantidad_input.value = ""
            lista_ingredientes.controls.clear()
            actualizar_lista_configuraciones_guardadas()  # ✅ ACTUALIZAR LISTA
            on_update_ui()
        except Exception as ex:
            print(f"Error al crear configuración: {ex}")

    def actualizar_lista_configuraciones_guardadas():
        try:
            configs = config_service.obtener_configuraciones()
            lista_configuraciones_guardadas.controls.clear()
            for config in configs:
                item_row = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{config['nombre']}", size=18, weight=ft.FontWeight.BOLD),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                on_click=lambda e, id=config['id']: eliminar_configuracion_click(id),
                                tooltip="Eliminar configuración",
                                icon_color=ft.Colors.RED_700
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"Descripción: {config['descripcion']}", size=14),
                        ft.Text("Ingredientes:", size=14, weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text(f"- {ing['nombre']}: {ing['cantidad']} {ing['unidad']}")
                            for ing in config['ingredientes']
                        ]),
                        ft.ElevatedButton(
                            "Aplicar configuración",
                            on_click=lambda e, id=config['id']: aplicar_configuracion_click(id),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
                        )
                    ]),
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    padding=10,
                    border_radius=10
                )
                lista_configuraciones_guardadas.controls.append(item_row)
            page.update()
        except Exception as e:
            print(f"Error al cargar configuraciones: {e}")

    # ✅ CARGAR CONFIGURACIONES AL INICIAR
    actualizar_lista_configuraciones_guardadas()

    vista = ft.Container(
        content=ft.Column([
            ft.Text("Configuraciones", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("Crear nueva configuración", size=18, weight=ft.FontWeight.BOLD),
            nombre_input,
            descripcion_input,
            ft.Divider(),
            ft.Text("Agregar ingredientes", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                nombre_ingrediente_input,
                cantidad_input,
                unidad_dropdown,
                ft.ElevatedButton(
                    "Agregar ingrediente",
                    on_click=agregar_ingrediente_click,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE)
                )
            ]),
            ft.Container(
                content=lista_ingredientes,
                bgcolor=ft.Colors.BLUE_GREY_800,
                padding=10,
                border_radius=5
            ),
            ft.ElevatedButton(
                "Crear configuración",
                on_click=crear_configuracion_click,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            ),
            ft.Divider(),
            ft.Text("Configuraciones guardadas", size=18, weight=ft.FontWeight.BOLD),
            lista_configuraciones_guardadas  # ✅ LISTA DE CONFIGURACIONES
        ]),
        padding=20,
        expand=True
    )

    vista.actualizar_lista_configuraciones_guardadas = actualizar_lista_configuraciones_guardadas  # ✅ AGREGAR FUNCIÓN
    return vista