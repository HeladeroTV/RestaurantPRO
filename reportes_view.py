# reportes_view.py
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

    # Contenedor para mostrar el reporte general
    contenedor_reporte = ft.Container(
        content=ft.Column(spacing=10),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10
    )

    # Contenedor para mostrar el análisis de productos
    contenedor_analisis = ft.Container(
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

            # Obtener datos del backend para el reporte general
            datos = backend_service.obtener_reporte(tipo, fecha)

            # Limpiar contenedor general
            contenedor_reporte.content.controls.clear()

            # Mostrar resumen general
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

            # Mostrar productos más vendidos del reporte general
            if datos.get('productos_mas_vendidos'):
                contenedor_reporte.content.controls.append(
                    ft.Divider()
                )
                contenedor_reporte.content.controls.append(
                    ft.Text("Productos más vendidos (General):", size=18, weight=ft.FontWeight.BOLD)
                )
                for producto in datos['productos_mas_vendidos']:
                    contenedor_reporte.content.controls.append(
                        ft.Text(f"- {producto['nombre']}: {producto['cantidad']} unidades")
                    )

            # --- ACTUALIZAR ANÁLISIS DE PRODUCTOS ---
            # Calcular rango de fechas para el análisis (similar al reporte general)
            start_date = None
            end_date = None
            if tipo == "Diario":
                start_date = fecha.strftime("%Y-%m-%d")
                end_date = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
            elif tipo == "Semanal":
                start_date = (fecha - timedelta(days=fecha.weekday())).strftime("%Y-%m-%d")
                end_date = (fecha + timedelta(days=6 - fecha.weekday())).strftime("%Y-%m-%d")
            elif tipo == "Mensual":
                start_date = fecha.replace(day=1).strftime("%Y-%m-%d")
                end_date = (fecha.replace(day=1) + timedelta(days=32)).replace(day=1).strftime("%Y-%m-%d")
            elif tipo == "Anual":
                start_date = fecha.replace(month=1, day=1).strftime("%Y-%m-%d")
                end_date = fecha.replace(month=12, day=31).strftime("%Y-%m-%d")

            # Limpiar contenedor de análisis
            contenedor_analisis.content.controls.clear()

            try:
                # Obtener datos del backend para el análisis
                datos_analisis = backend_service.obtener_analisis_productos(start_date=start_date, end_date=end_date)

                # Mostrar encabezado del análisis
                contenedor_analisis.content.controls.append(
                    ft.Text(f"Análisis de Productos - {tipo} ({start_date} a {end_date})", size=20, weight=ft.FontWeight.BOLD)
                )
                contenedor_analisis.content.controls.append(
                    ft.Divider()
                )

                # Mostrar productos más vendidos
                if datos_analisis.get('productos_mas_vendidos'):
                    contenedor_analisis.content.controls.append(
                        ft.Text("Productos más vendidos:", size=18, weight=ft.FontWeight.BOLD)
                    )
                    for producto in datos_analisis['productos_mas_vendidos']:
                        contenedor_analisis.content.controls.append(
                            ft.Text(f"- {producto['nombre']}: {producto['cantidad']} veces")
                        )
                else:
                    contenedor_analisis.content.controls.append(
                        ft.Text("No se encontraron productos vendidos en este periodo.", size=14, italic=True)
                    )

                contenedor_analisis.content.controls.append(
                    ft.Divider()
                )

                # Mostrar productos menos vendidos
                if datos_analisis.get('productos_menos_vendidos'):
                    contenedor_analisis.content.controls.append(
                        ft.Text("Productos menos vendidos:", size=18, weight=ft.FontWeight.BOLD)
                    )
                    for producto in datos_analisis['productos_menos_vendidos']:
                        contenedor_analisis.content.controls.append(
                            ft.Text(f"- {producto['nombre']}: {producto['cantidad']} veces")
                        )
                else:
                    contenedor_analisis.content.controls.append(
                        ft.Text("No se encontraron productos menos vendidos en este periodo.", size=14, italic=True)
                    )

            except Exception as ex:
                print(f"Error al obtener análisis de productos: {ex}")
                contenedor_analisis.content.controls.append(
                    ft.Text(f"Error al cargar análisis de productos: {ex}", color=ft.Colors.RED)
                )

            page.update()
        except Exception as ex:
            print(f"Error al actualizar reporte general: {ex}")

    # Configurar DatePicker
    fecha_picker.on_change = lambda e: setattr(fecha_text, 'value', f"Fecha: {e.control.value.strftime('%Y-%m-%d')}") or page.update()

    # Vista principal: Envolver la Columna en un Scrollview
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
            contenedor_reporte, # Contenedor del reporte general
            ft.Divider(),
            contenedor_analisis # Contenedor del análisis de productos
        ], scroll="auto"), # <-- AÑADIR scroll="auto" A LA COLUMNA
        padding=20,
        expand=True
    )

    return vista