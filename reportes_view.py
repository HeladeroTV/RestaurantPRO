import flet as ft
from typing import List, Dict, Any
from datetime import datetime, timedelta

def crear_vista_reportes(backend_service, on_update_ui, page):
    # Dropdown para seleccionar el tipo de reporte
    tipo_reporte_dropdown = ft.Dropdown(
        label="Tipo de reporte",
        options=[
            ft.dropdown.Option("Diario"),
            ft.dropdown.Option("Semanal"),
            ft.dropdown.Option("Mensual"),
            ft.dropdown.Option("Anual"),
        ],
        value="Diario",
        width=200
    )

    # DatePicker para seleccionar la fecha
    fecha_picker = ft.DatePicker(
        on_change=lambda e: actualizar_reporte(None)
    )
    fecha_button = ft.ElevatedButton(
        "Seleccionar fecha",
        icon=ft.Icons.CALENDAR_TODAY,
        on_click=lambda _: page.open(fecha_picker)
    )
    fecha_text = ft.Text("Fecha: Hoy", size=16)

    # Contenedor para mostrar el reporte
    contenedor_reporte = ft.Container(
        content=ft.Column(spacing=10),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10
    )

    def actualizar_reporte(e):
        try:
            # Obtener tipo de reporte y fecha
            tipo = tipo_reporte_dropdown.value
            fecha_str = fecha_text.value.split(": ")[1]

            # Convertir fecha a objeto datetime
            if fecha_str == "Hoy":
                fecha = datetime.now()
            else:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")

            # Obtener datos del backend
            datos = backend_service.obtener_reporte(tipo, fecha)

            # Limpiar contenedor
            contenedor_reporte.content.controls.clear()

            # Mostrar resumen
            contenedor_reporte.content.controls.append(
                ft.Text(f"Reporte {tipo} - {fecha_str}", size=20, weight=ft.FontWeight.BOLD)
            )
            contenedor_reporte.content.controls.append(
                ft.Divider()
            )

            # Mostrar totales
            contenedor_reporte.content.controls.append(
                ft.Text(f"Ventas totales: ${datos.get('ventas_totales', 0):.2f}", size=16)
            )
            contenedor_reporte.content.controls.append(
                ft.Text(f"Pedidos totales: {datos.get('pedidos_totales', 0)}", size=16)
            )
            contenedor_reporte.content.controls.append(
                ft.Text(f"Productos vendidos: {datos.get('productos_vendidos', 0)}", size=16)
            )

            # Mostrar productos más vendidos
            if datos.get('productos_mas_vendidos'):
                contenedor_reporte.content.controls.append(
                    ft.Divider()
                )
                contenedor_reporte.content.controls.append(
                    ft.Text("Productos más vendidos:", size=18, weight=ft.FontWeight.BOLD)
                )
                for producto in datos['productos_mas_vendidos']:
                    contenedor_reporte.content.controls.append(
                        ft.Text(f"- {producto['nombre']}: {producto['cantidad']} unidades")
                    )

            page.update()
        except Exception as ex:
            print(f"Error al actualizar reporte: {ex}")

    # Configurar DatePicker
    fecha_picker.on_change = lambda e: setattr(fecha_text, 'value', f"Fecha: {e.control.value.strftime('%Y-%m-%d')}") or page.update()

    vista = ft.Container(
        content=ft.Column([
            ft.Text("Reportes", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                tipo_reporte_dropdown,
                fecha_button,
                fecha_text
            ]),
            ft.ElevatedButton(
                "Actualizar reporte",
                on_click=actualizar_reporte,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            ),
            ft.Divider(),
            contenedor_reporte
        ]),
        padding=20,
        expand=True
    )

    return vista