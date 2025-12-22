# reportes_view.py
import flet as ft
# --- IMPORTAR PLOTLY Y IO ---
import plotly.graph_objects as go
import plotly.express as px
import io
import base64
# --- FIN IMPORTAR ---
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
        on_change=lambda e: setattr(fecha_text, 'value', f"Fecha: {e.control.value.strftime('%Y-%m-%d')}") or page.update()
    )
    fecha_button = ft.ElevatedButton(
        "Seleccionar fecha",
        icon=ft.Icons.CALENDAR_TODAY,
        on_click=lambda _: page.open(fecha_picker)
    )
    fecha_text = ft.Text("Fecha: Hoy", size=16)

    # Contenedor para mostrar el reporte general (EXISTENTE)
    contenedor_reporte = ft.Container(
        content=ft.Column(spacing=10),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10
    )

    # Contenedor para mostrar el análisis de productos (EXISTENTE)
    contenedor_analisis = ft.Container(
        content=ft.Column(spacing=10),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10
    )

    # --- CREAR CONTROLES DE IMAGEN PARA LOS GRÁFICOS ---
    # Asegúrate de que estos controles tengan un tamaño fijo o expandan correctamente
    imagen_resumen = ft.Image(
        # src="", # Se actualizará con base64
        fit=ft.ImageFit.CONTAIN,
        width=600, # Ajusta según necesites
        height=300,
    )

    imagen_productos_vendidos = ft.Image(
        fit=ft.ImageFit.CONTAIN,
        width=600,
        height=300,
    )

    imagen_ventas_hora = ft.Image(
        fit=ft.ImageFit.CONTAIN,
        width=600,
        height=300,
    )

    imagen_analisis_mas = ft.Image(
        fit=ft.ImageFit.CONTAIN,
        width=600,
        height=300,
    )

    imagen_analisis_menos = ft.Image(
        fit=ft.ImageFit.CONTAIN,
        width=600,
        height=300,
    )
    # --- FIN CREAR CONTROLES DE IMAGEN ---

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

            # --- OBTENER VENTAS POR HORA ---
            ventas_por_hora = backend_service.obtener_ventas_por_hora(fecha.strftime("%Y-%m-%d"))
            # --- FIN OBTENER VENTAS POR HORA ---

            # Obtener datos del backend para el reporte general
            datos = backend_service.obtener_reporte(tipo, fecha)

            # Limpiar contenedor general (solo los elementos de texto existentes)
            controles_texto = []
            controles_texto.append(ft.Text(f"Reporte {tipo} - {fecha_str}", size=20, weight=ft.FontWeight.BOLD))
            controles_texto.append(ft.Divider())
            controles_texto.append(ft.Text(f"Ventas totales: ${datos.get('ventas_totales', 0):.2f}", size=16))
            controles_texto.append(ft.Text(f"Pedidos totales: {datos.get('pedidos_totales', 0)}", size=16))
            controles_texto.append(ft.Text(f"Productos vendidos: {datos.get('productos_vendidos', 0)}", size=16))

            if datos.get('productos_mas_vendidos'):
                controles_texto.append(ft.Divider())
                controles_texto.append(ft.Text("Productos más vendidos (General):", size=18, weight=ft.FontWeight.BOLD))
                for producto in datos['productos_mas_vendidos']:
                    controles_texto.append(ft.Text(f"- {producto['nombre']}: {producto['cantidad']} unidades"))

            controles_texto.append(ft.Divider())
            controles_texto.append(ft.Text("Ventas por Hora:", size=18, weight=ft.FontWeight.BOLD))
            horas_con_venta = {h: v for h, v in ventas_por_hora.items() if v > 0}
            if horas_con_venta:
                for hora_str, total in sorted(horas_con_venta.items()):
                    controles_texto.append(ft.Text(f"Hora {hora_str.zfill(2)}:00 - ${total:.2f}"))
            else:
                controles_texto.append(ft.Text("No hubo ventas en esta fecha.", size=14, italic=True))

            # --- GENERAR Y ACTUALIZAR GRÁFICOS CON PLOTLY ---
            # 1. Gráfico de Resumen General (Ventas, Pedidos, Productos)
            if datos.get('ventas_totales') is not None and datos.get('pedidos_totales') is not None and datos.get('productos_vendidos') is not None:
                fig_resumen = go.Figure(data=[
                    go.Bar(name='Ventas ($)', x=['Resumen'], y=[datos.get('ventas_totales', 0)], text=[f"${datos.get('ventas_totales', 0):.2f}"], textposition='auto'),
                    go.Bar(name='Pedidos', x=['Resumen'], y=[datos.get('pedidos_totales', 0)], text=[datos.get('pedidos_totales', 0)], textposition='auto'),
                    go.Bar(name='Productos', x=['Resumen'], y=[datos.get('productos_vendidos', 0)], text=[datos.get('productos_vendidos', 0)], textposition='auto')
                ])
                fig_resumen.update_layout(title_text='Resumen General', height=300)
                # Convertir a bytes y actualizar imagen
                img_bytes_resumen = fig_resumen.to_image(format="png", width=600, height=300, scale=1)
                imagen_resumen.src_base64 = base64.b64encode(img_bytes_resumen).decode('utf-8')
            else:
                imagen_resumen.src_base64 = "" # Limpiar si no hay datos
                print("Advertencia: Datos de resumen general incompletos.")


            # 2. Gráfico de Productos Más Vendidos
            if datos.get('productos_mas_vendidos'):
                nombres_pv = [p['nombre'] for p in datos['productos_mas_vendidos']]
                cantidades_pv = [p['cantidad'] for p in datos['productos_mas_vendidos']]
                fig_pv = px.bar(x=cantidades_pv, y=nombres_pv, orientation='h', title='Productos Más Vendidos (General)', labels={'x': 'Cantidad', 'y': 'Producto'})
                fig_pv.update_layout(height=300)
                # Convertir a bytes y actualizar imagen
                img_bytes_pv = fig_pv.to_image(format="png", width=600, height=300, scale=1)
                imagen_productos_vendidos.src_base64 = base64.b64encode(img_bytes_pv).decode('utf-8')
            else:
                 imagen_productos_vendidos.src_base64 = "" # Limpiar si no hay datos

            # 3. Gráfico de Ventas por Hora
            horas_ordenadas = sorted(ventas_por_hora.keys(), key=int)
            horas_con_venta_datos = {h: v for h, v in ventas_por_hora.items() if v > 0}
            if horas_con_venta_datos:
                horas_plot = [f"{h}h" for h in sorted(horas_con_venta_datos.keys(), key=int)]
                ventas_plot = [horas_con_venta_datos[h] for h in sorted(horas_con_venta_datos.keys(), key=int)]
                fig_hora = go.Figure(data=go.Scatter(x=horas_plot, y=ventas_plot, mode='lines+markers', name='Ventas por Hora'))
                fig_hora.update_layout(title='Ventas por Hora', xaxis_title='Hora del Día', yaxis_title='Ventas ($)', height=300)
                # Convertir a bytes y actualizar imagen
                img_bytes_hora = fig_hora.to_image(format="png", width=600, height=300, scale=1)
                imagen_ventas_hora.src_base64 = base64.b64encode(img_bytes_hora).decode('utf-8')
            else:
                 imagen_ventas_hora.src_base64 = "" # Limpiar si no hay datos


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

            # Limpiar contenedor de análisis (solo texto)
            controles_analisis_texto = []
            controles_analisis_texto.append(ft.Text(f"Análisis de Productos - {tipo} ({start_date} a {end_date})", size=20, weight=ft.FontWeight.BOLD))
            controles_analisis_texto.append(ft.Divider())

            try:
                # Obtener datos del backend para el análisis
                datos_analisis = backend_service.obtener_analisis_productos(start_date=start_date, end_date=end_date)

                # Mostrar productos más vendidos
                if datos_analisis.get('productos_mas_vendidos'):
                    controles_analisis_texto.append(ft.Text("Productos más vendidos:", size=18, weight=ft.FontWeight.BOLD))
                    for producto in datos_analisis['productos_mas_vendidos']:
                        controles_analisis_texto.append(ft.Text(f"- {producto['nombre']}: {producto['cantidad']} veces"))
                else:
                    controles_analisis_texto.append(ft.Text("No se encontraron productos vendidos en este periodo.", size=14, italic=True))

                controles_analisis_texto.append(ft.Divider())

                # Mostrar productos menos vendidos
                if datos_analisis.get('productos_menos_vendidos'):
                    controles_analisis_texto.append(ft.Text("Productos menos vendidos:", size=18, weight=ft.FontWeight.BOLD))
                    for producto in datos_analisis['productos_menos_vendidos']:
                        controles_analisis_texto.append(ft.Text(f"- {producto['nombre']}: {producto['cantidad']} veces"))
                else:
                    controles_analisis_texto.append(ft.Text("No se encontraron productos menos vendidos en este periodo.", size=14, italic=True))

            except Exception as ex:
                print(f"Error al obtener análisis de productos: {ex}")
                controles_analisis_texto.append(ft.Text(f"Error al cargar análisis de productos: {ex}", color=ft.Colors.RED))

            # --- GENERAR Y ACTUALIZAR GRÁFICOS DE ANÁLISIS CON PLOTLY ---
            # 4. Gráfico de Análisis - Más Vendidos
            if datos_analisis.get('productos_mas_vendidos'):
                nombres_am = [p['nombre'] for p in datos_analisis['productos_mas_vendidos']]
                cantidades_am = [p['cantidad'] for p in datos_analisis['productos_mas_vendidos']]
                fig_am = px.bar(x=cantidades_am, y=nombres_am, orientation='h', title='Análisis - Más Vendidos', labels={'x': 'Cantidad', 'y': 'Producto'})
                fig_am.update_layout(height=300)
                # Convertir a bytes y actualizar imagen
                img_bytes_am = fig_am.to_image(format="png", width=600, height=300, scale=1)
                imagen_analisis_mas.src_base64 = base64.b64encode(img_bytes_am).decode('utf-8')
            else:
                 imagen_analisis_mas.src_base64 = "" # Limpiar si no hay datos

            # 5. Gráfico de Análisis - Menos Vendidos
            if datos_analisis.get('productos_menos_vendidos'):
                nombres_anm = [p['nombre'] for p in datos_analisis['productos_menos_vendidos']]
                cantidades_anm = [p['cantidad'] for p in datos_analisis['productos_menos_vendidos']]
                fig_anm = px.bar(x=cantidades_anm, y=nombres_anm, orientation='h', title='Análisis - Menos Vendidos', labels={'x': 'Cantidad', 'y': 'Producto'})
                fig_anm.update_layout(height=300)
                # Convertir a bytes y actualizar imagen
                img_bytes_anm = fig_anm.to_image(format="png", width=600, height=300, scale=1)
                imagen_analisis_menos.src_base64 = base64.b64encode(img_bytes_anm).decode('utf-8')
            else:
                 imagen_analisis_menos.src_base64 = "" # Limpiar si no hay datos


            # Reconstruir contenedor_reporte con texto y gráficos (imagen)
            contenedor_reporte.content.controls = controles_texto + [
                ft.Text("Gráfico Resumen General", size=16, weight=ft.FontWeight.BOLD),
                imagen_resumen,
                ft.Text("Gráfico Productos Más Vendidos", size=16, weight=ft.FontWeight.BOLD),
                imagen_productos_vendidos,
                ft.Text("Gráfico Ventas por Hora", size=16, weight=ft.FontWeight.BOLD),
                imagen_ventas_hora,
            ]

            # Reconstruir contenedor_analisis con texto y gráficos (imagen)
            contenedor_analisis.content.controls = controles_analisis_texto + [
                ft.Text("Gráfico Análisis - Más Vendidos", size=16, weight=ft.FontWeight.BOLD),
                imagen_analisis_mas,
                ft.Text("Gráfico Análisis - Menos Vendidos", size=16, weight=ft.FontWeight.BOLD),
                imagen_analisis_menos,
            ]

            # --- FIN ACTUALIZAR DATOS DE LOS GRÁFICOS ---

            page.update()
        except Exception as ex:
            print(f"Error al actualizar reporte general: {ex}")
            import traceback
            traceback.print_exc() # Imprime el traceback completo para depuración
            # Opcional: Mostrar error en la UI
            contenedor_reporte.content.controls.clear()
            contenedor_reporte.content.controls.append(
                ft.Text(f"Error al cargar reporte: {ex}", color=ft.Colors.RED)
            )
            contenedor_analisis.content.controls.clear()
            contenedor_analisis.content.controls.append(
                ft.Text(f"Error al cargar análisis: {ex}", color=ft.Colors.RED)
            )
            # Limpiar imágenes en caso de error
            imagen_resumen.src_base64 = ""
            imagen_productos_vendidos.src_base64 = ""
            imagen_ventas_hora.src_base64 = ""
            imagen_analisis_mas.src_base64 = ""
            imagen_analisis_menos.src_base64 = ""
            page.update()


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
            contenedor_reporte, # Contenedor del reporte general (ahora incluye imágenes de gráficos)
            ft.Divider(),
            contenedor_analisis # Contenedor del análisis de productos (ahora incluye imágenes de gráficos)
        ], scroll="auto"), # <-- AÑADIR scroll="auto" A LA COLUMNA
        padding=20,
        expand=True
    )

    return vista