import flet as ft
from typing import List, Dict, Any

def crear_vista_recetas(recetas_service, on_update_ui, page):
    # Campos de entrada
    nombre_input = ft.TextField(label="Nombre de la receta", width=300)
    descripcion_input = ft.TextField(label="Descripción", multiline=True, width=300)

    # Dropdown para seleccionar ingredientes
    ingrediente_dropdown = ft.Dropdown(
        label="Seleccionar ingrediente",
        width=200
    )

    # Campo para cantidad de ingrediente
    cantidad_input = ft.TextField(
        label="Cantidad necesaria",
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

    # Lista de ingredientes de la receta
    lista_ingredientes = ft.Column(spacing=5)

    # Lista de recetas
    lista_recetas = ft.ListView(
        expand=1,
        spacing=10,
        padding=20,
        auto_scroll=True,
    )

    def cargar_ingredientes_dropdown():
        try:
            # Aquí puedes obtener los ingredientes del inventario
            # Suponiendo que tienes un servicio de inventario
            from inventario_service import InventoryService
            inv_service = InventoryService()
            items = inv_service.obtener_inventario()
            ingrediente_dropdown.options = [
                ft.dropdown.Option(item['nombre'], key=str(item['id']))
                for item in items
            ]
            page.update()
        except Exception as e:
            print(f"Error al cargar ingredientes: {e}")

    def agregar_ingrediente_click(e):
        nombre_ing = ingrediente_dropdown.value
        id_ing = ingrediente_dropdown.value  # Aquí debes obtener el ID real
        cantidad = cantidad_input.value
        unidad = unidad_dropdown.value

        if not nombre_ing or not cantidad:
            return

        # Aquí debes buscar el ID real del ingrediente
        from inventario_service import InventoryService
        inv_service = InventoryService()
        items = inv_service.obtener_inventario()
        id_ing = None
        for item in items:
            if item['nombre'] == nombre_ing:
                id_ing = item['id']
                break

        if not id_ing:
            return

        item_row = ft.Container(
            content=ft.Row([
                ft.Text(f"{nombre_ing} - {cantidad} {unidad}"),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    on_click=lambda e, id=id_ing: eliminar_ingrediente_click(id)
                )
            ]),
            bgcolor=ft.Colors.BLUE_GREY_800,
            padding=5,
            border_radius=5
        )
        lista_ingredientes.controls.append(item_row)
        page.update()

    def eliminar_ingrediente_click(ingrediente_id: int):
        # Eliminar de la lista visual
        lista_ingredientes.controls = [
            c for c in lista_ingredientes.controls
            if c.content.controls[0].value.split(" - ")[0] != str(ingrediente_id)
        ]
        page.update()

    def crear_receta_click(e):
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
                "ingrediente_id": int(nombre_ing),  # Aquí debes usar el ID real
                "cantidad_necesaria": int(cantidad),
                "unidad": unidad
            })

        try:
            recetas_service.crear_receta(nombre, descripcion, ingredientes)
            nombre_input.value = ""
            descripcion_input.value = ""
            lista_ingredientes.controls.clear()
            on_update_ui()
        except Exception as ex:
            print(f"Error al crear receta: {ex}")

    def actualizar_lista():
        try:
            recetas = recetas_service.obtener_recetas()
            lista_recetas.controls.clear()
            for receta in recetas:
                item_row = ft.Container(
                    content=ft.Column([
                        ft.Text(f"{receta['nombre']}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Descripción: {receta['descripcion']}", size=14),
                        ft.Text("Ingredientes:", size=14, weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text(f"- {ing['nombre']}: {ing['cantidad_necesaria']} {ing['unidad']}")
                            for ing in receta['ingredientes']
                        ]),
                        ft.ElevatedButton(
                            "Eliminar",
                            on_click=lambda e, id=receta['id']: eliminar_receta_click(id),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                        )
                    ]),
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    padding=10,
                    border_radius=10
                )
                lista_recetas.controls.append(item_row)
            page.update()
        except Exception as e:
            print(f"Error al cargar recetas: {e}")

    def eliminar_receta_click(receta_id: int):
        try:
            recetas_service.eliminar_receta(receta_id)
            on_update_ui()
        except Exception as ex:
            print(f"Error al eliminar receta: {ex}")

    vista = ft.Container(
        content=ft.Column([
            ft.Text("Recetas", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("Crear nueva receta", size=18, weight=ft.FontWeight.BOLD),
            nombre_input,
            descripcion_input,
            ft.Divider(),
            ft.Text("Agregar ingredientes", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                ingrediente_dropdown,
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
                "Crear receta",
                on_click=crear_receta_click,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            ),
            ft.Divider(),
            ft.Text("Recetas registradas", size=18, weight=ft.FontWeight.BOLD),
            lista_recetas
        ]),
        padding=20,
        expand=True
    )

    vista.actualizar_lista = actualizar_lista
    return vista