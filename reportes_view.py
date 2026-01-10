# reportes_view.py
import flet as ft
# --- IMPORTAR PLOTLY Y IO ---
import plotly.graph_objects as go
import plotly.express as px
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
# --- FIN IMPORTAR ---
from typing import List, Dict, Any
from datetime import datetime, timedelta
import math

def crear_dashboard_ejecutivo(datos_comparativos, tipo_reporte):
    """Crea el dashboard ejecutivo con KPIs y comparativas"""
    
    actual = datos_comparativos.get("actual", {})
    anterior = datos_comparativos.get("anterior", {})
    
    # Calcular KPIs principales
    ventas_actuales = actual.get("ventas_totales", 0)
    ventas_anteriores = anterior.get("ventas_totales", 0)
    pedidos_actuales = actual.get("pedidos_totales", 1)  # Evitar división por cero
    pedidos_anteriores = anterior.get("pedidos_totales", 1)
    productos_actuales = actual.get("productos_vendidos", 0)
    productos_anteriores = anterior.get("productos_vendidos", 0)
    
    # Calcular variaciones
    var_ventas = ((ventas_actuales - ventas_anteriores) / ventas_anteriores * 100) if ventas_anteriores > 0 else 0
    var_pedidos = ((pedidos_actuales - pedidos_anteriores) / pedidos_anteriores * 100) if pedidos_anteriores > 0 else 0
    var_productos = ((productos_actuales - productos_anteriores) / productos_anteriores * 100) if productos_anteriores > 0 else 0
    
    # Calcular KPIs adicionales
    ticket_promedio_actual = ventas_actuales / pedidos_actuales if pedidos_actuales > 0 else 0
    ticket_promedio_anterior = ventas_anteriores / pedidos_anteriores if pedidos_anteriores > 0 else 0
    var_ticket = ((ticket_promedio_actual - ticket_promedio_anterior) / ticket_promedio_anterior * 100) if ticket_promedio_anterior > 0 else 0
    
    # Crear tarjetas KPI
    def crear_tarjeta_kpi(titulo, valor, variacion, descripcion="", color_base=ft.Colors.BLUE):
        # Determinar color según variación
        if variacion > 0:
            color_var = ft.Colors.GREEN_500
            icono = ft.Icons.ARROW_UPWARD
        elif variacion < 0:
            color_var = ft.Colors.RED_500
            icono = ft.Icons.ARROW_DOWNWARD
        else:
            color_var = ft.Colors.GREY_500
            icono = ft.Icons.ARROW_FORWARD
        
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=14, color=ft.Colors.GREY_400),
                ft.Row([
                    ft.Text(f"${valor:,.2f}" if isinstance(valor, (int, float)) and titulo == "Ventas Totales" else f"{valor:,}" if isinstance(valor, (int, float)) else str(valor), 
                           size=24, weight=ft.FontWeight.BOLD),
                    ft.Icon(icono, color=color_var, size=20) if variacion != 0 else ft.Text("")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(f"{variacion:+.1f}%" if variacion != 0 else "Sin cambio", 
                       size=12, color=color_var),
                ft.Text(descripcion, size=11, color=ft.Colors.GREY_500) if descripcion else ft.Text("")
            ], spacing=5),
            padding=15,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_GREY_800,
            width=200,
            height=120
        )
    
    # Tarjetas KPI principales
    kpi_ventas = crear_tarjeta_kpi(
        "Ventas Totales", 
        ventas_actuales, 
        var_ventas,
        f"vs período anterior"
    )
    
    kpi_pedidos = crear_tarjeta_kpi(
        "Pedidos Totales", 
        pedidos_actuales, 
        var_pedidos,
        f"vs período anterior"
    )
    
    kpi_ticket = crear_tarjeta_kpi(
        "Ticket Promedio", 
        ticket_promedio_actual, 
        var_ticket,
        f"vs período anterior"
    )
    
    kpi_productos = crear_tarjeta_kpi(
        "Productos Vendidos", 
        productos_actuales, 
        var_productos,
        f"vs período anterior"
    )
    
    # Dashboard container
    dashboard_container = ft.Container(
        content=ft.Column([
            ft.Text(f"Dashboard Ejecutivo - {tipo_reporte}", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                kpi_ventas,
                kpi_pedidos,
                kpi_ticket,
                kpi_productos
            ], wrap=True, spacing=10),
        ], spacing=10),
        padding=20,
        border_radius=10,
        bgcolor=ft.Colors.BLUE_GREY_900
    )
    
    return dashboard_container

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

    def on_fecha_change(e):
        if e.control.value:
            fecha_text.value = f"Fecha: {e.control.value.strftime('%Y-%m-%d')}"
            page.update()

    fecha_picker = ft.DatePicker(on_change=on_fecha_change)
    fecha_button = ft.ElevatedButton(
        "Seleccionar fecha",
        icon=ft.Icons.CALENDAR_TODAY,
        on_click=lambda _: page.open(fecha_picker)
    )
    fecha_text = ft.Text("Fecha: Hoy", size=16)

    # --- DATOS PARA PDF (Variable de estado) ---
    # Almacenaremos los bytes de las imágenes y los textos para usarlos en el PDF
    estado_reporte = {
        "tipo": "",
        "fecha": "",
        "textos": [],
        "img_resumen": None,
        "img_productos": None,
        "img_horas": None,
        "img_analisis_mas": None,
        "img_analisis_menos": None,
        "img_eficiencia": None
    }

    def guardar_pdf(e: ft.FilePickerResultEvent):
        if e.path:
            try:
                c = canvas.Canvas(e.path, pagesize=letter)
                width, height = letter
                
                # Encabezado
                c.setFont("Helvetica-Bold", 18)
                c.drawString(50, height - 50, f"Reporte {estado_reporte['tipo']}")
                c.setFont("Helvetica", 12)
                c.drawString(50, height - 70, f"Fecha: {estado_reporte['fecha']}")
                
                # Textos Resumen
                y = height - 100
                c.setFont("Helvetica", 10)
                for linea in estado_reporte["textos"]:
                    # Ignorar algunas líneas decorativas o repetitivas si se desea
                    if isinstance(linea, str) and "---" not in linea:
                         c.drawString(50, y, linea)
                         y -= 15
                    if y < 50: # Nueva página si se acaba el espacio
                        c.showPage()
                        y = height - 50

                # Función auxiliar para dibujar imagen
                def dibujar_imagen(img_bytes, x, y, w, h):
                    if img_bytes:
                        try:
                            # Plotly to_image devuelve bytes, ReportLab ImageReader los puede leer
                            image = ImageReader(io.BytesIO(img_bytes))
                            c.drawImage(image, x, y, width=w, height=h)
                            return True
                        except Exception as ex:
                            print(f"Error dibujando imagen: {ex}")
                    return False

                # Gráficos
                # Resumen
                y -= 20
                if estado_reporte['img_resumen']:
                    c.drawString(50, y, "Resumen General")
                    y -= 210
                    dibujar_imagen(estado_reporte['img_resumen'], 50, y, 500, 200)
                    y -= 30
                
                if y < 250: c.showPage(); y = height - 50

                # Productos
                if estado_reporte['img_productos']:
                    c.drawString(50, y, "Productos Más Vendidos")
                    y -= 210
                    dibujar_imagen(estado_reporte['img_productos'], 50, y, 500, 200)
                    y -= 30

                if y < 250: c.showPage(); y = height - 50
                
                # Ventas Hora
                if estado_reporte['img_horas']:
                     c.drawString(50, y, "Ventas por Hora")
                     y -= 210
                     dibujar_imagen(estado_reporte['img_horas'], 50, y, 500, 200)
                     y -= 30

                if y < 250: c.showPage(); y = height - 50

                # Eficiencia
                if estado_reporte['img_eficiencia']:
                     c.drawString(50, y, "Eficiencia de Cocina")
                     y -= 210
                     dibujar_imagen(estado_reporte['img_eficiencia'], 50, y, 500, 200)
                     y -= 30

                c.save()
                
                # Mostrar confirmación
                page.snack_bar = ft.SnackBar(ft.Text(f"Reporte guardado en: {e.path}"))
                page.snack_bar.open = True
                page.update()

            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error al guardar PDF: {ex}"))
                page.snack_bar.open = True
                page.update()
                print(f"Error PDF: {ex}")

    file_picker = ft.FilePicker(on_result=guardar_pdf)
    page.overlay.append(file_picker)

    def exportar_pdf_click(e):
        # Abrir diálogo para guardar archivo
        file_picker.save_file(
            dialog_title="Guardar Reporte como PDF",
            file_name=f"Reporte_{estado_reporte['tipo']}_{estado_reporte['fecha'].replace(':', '-')}.pdf",
            allowed_extensions=["pdf"]
        )

    # --- FIN EXPORTAR PDF ---
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

    # --- NUEVO: Controles para eficiencia de cocina ---
    texto_eficiencia_cocina = ft.Text("", size=16) # Para mostrar el promedio como texto
    imagen_eficiencia_cocina = ft.Image( # Para mostrar un gráfico de eficiencia
        fit=ft.ImageFit.CONTAIN,
        width=600,
        height=300,
    )
    contenedor_eficiencia_cocina = ft.Container(
        content=ft.Column([
            ft.Text("Eficiencia de Cocina", size=18, weight=ft.FontWeight.BOLD),
            texto_eficiencia_cocina,
            imagen_eficiencia_cocina
        ]),
        bgcolor=ft.Colors.BLUE_GREY_800,
        padding=10,
        border_radius=5,
        visible=True
    )
    # --- FIN NUEVO ---

    def actualizar_reporte(e):
        try:
            # Obtener tipo de reporte y fecha
            tipo = tipo_reporte_dropdown.value
            # CORRECCIÓN: Extraer la fecha de manera más robusta
            fecha_text_content = fecha_text.value.strip()
            if ": " in fecha_text_content:
                fecha_str = fecha_text_content.split(": ", 1)[1].strip()
            else:
                fecha_str = fecha_text_content

            # Convertir fecha a objeto datetime
            if fecha_str.lower() == "hoy" or fecha_str == "":
                fecha = datetime.now()
            else:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")

            # --- OBTENER VENTAS POR HORA ---
            ventas_por_hora = backend_service.obtener_ventas_por_hora(fecha.strftime("%Y-%m-%d"))
            # --- FIN OBTENER VENTAS POR HORA ---

            # Obtener datos del backend para el reporte general
            datos = backend_service.obtener_reporte(tipo, fecha)

            # ================================================
            # 📌 OBTENER DATOS COMPARATIVOS REALES
            # ================================================

            try:
                datos_comparativos = backend_service.obtener_reporte_comparativo(tipo, fecha)
            except Exception as e:
                print(f"Error obteniendo datos comparativos: {e}")
                # Fallback con datos simulados
                datos_comparativos = {
                    "actual": datos,
                    "anterior": {
                        "ventas_totales": datos.get("ventas_totales", 0) * 0.85,
                        "pedidos_totales": max(1, int(datos.get("pedidos_totales", 0) * 0.9)),
                        "productos_vendidos": int(datos.get("productos_vendidos", 0) * 0.88)
                    }
                }
            
            # Crear dashboard ejecutivo
            dashboard_ejecutivo = crear_dashboard_ejecutivo(datos_comparativos, tipo)
            
            # ================================================
            # FIN OBTENER DATOS COMPARATIVOS
            # ================================================

            start_date = None
            end_date = None

            if tipo == "Diario":
                start_date = fecha.strftime("%Y-%m-%d")
                end_date = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
            elif tipo == "Semanal":
                # Calcular lunes de la semana
                start_of_week = fecha - timedelta(days=fecha.weekday())
                start_date = start_of_week.strftime("%Y-%m-%d")
                end_date = (start_of_week + timedelta(days=6)).strftime("%Y-%m-%d")
            elif tipo == "Mensual":
                # Primer día del mes
                start_date = fecha.replace(day=1).strftime("%Y-%m-%d")
                # Último día del mes
                if fecha.month == 12:
                    end_date = fecha.replace(day=31).strftime("%Y-%m-%d")
                else:
                    # Primer día del siguiente mes - 1 día
                    next_month = fecha.replace(day=1) + timedelta(days=32)
                    end_date = (next_month.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
            elif tipo == "Anual":
                start_date = fecha.replace(month=1, day=1).strftime("%Y-%m-%d")
                end_date = fecha.replace(month=12, day=31).strftime("%Y-%m-%d")
            else:
                # Default a diario si el tipo no coincide
                start_date = fecha.strftime("%Y-%m-%d")
                end_date = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
            # ================================================

            # Obtener datos de eficiencia de cocina (simulado si no existe)
            try:
                datos_eficiencia = backend_service.obtener_eficiencia_cocina(tipo, fecha)
                promedio_cocina_min = datos_eficiencia.get("promedio_minutos", 0)
                detalle_pedidos_cocina = datos_eficiencia.get("detalle_pedidos", [])
            except AttributeError:
                print("Método backend_service.obtener_eficiencia_cocina no encontrado. Debes crearlo.")
                promedio_cocina_min = 0
                detalle_pedidos_cocina = []
            except Exception as ex:
                print(f"Error al obtener datos de eficiencia de cocina: {ex}")
                promedio_cocina_min = 0
                detalle_pedidos_cocina = []

            # --- FIN CALCULAR EFICIENCIA DE COCINA ---


            # --- GUARDAR DATOS EN ESTADO PARA PDF ---
            estado_reporte["tipo"] = tipo
            estado_reporte["fecha"] = fecha_str
            estado_reporte["textos"] = [] # Se llenará abajo
            # ----------------------------------------

            # Limpiar contenedor general (solo los elementos de texto existentes)
            controles_texto = []
            controles_texto.append(ft.Text(f"Reporte {tipo} - {fecha_str}", size=20, weight=ft.FontWeight.BOLD))
            controles_texto.append(ft.Divider())
            controles_texto.append(ft.Text(f"Ventas totales: ${datos.get('ventas_totales', 0):.2f}", size=16))
            controles_texto.append(ft.Text(f"Pedidos totales: {datos.get('pedidos_totales', 0)}", size=16))
            controles_texto.append(ft.Text(f"Productos vendidos: {datos.get('productos_vendidos', 0)}", size=16))

            # --- AÑADIR EFICIENCIA DE COCINA A LOS CONTROLES DE TEXTO ---
            controles_texto.append(ft.Text(f"Tiempo promedio en cocina: {promedio_cocina_min:.2f} minutos", size=16, weight=ft.FontWeight.BOLD))
            # --- FIN AÑADIR ---

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
                
                # --- LLENAR ESTADO DE TEXTOS PARA PDF ---
                # Extraemos el valor string de los controles de texto para el PDF
                for control in controles_texto:
                    if isinstance(control, ft.Text):
                        estado_reporte["textos"].append(control.value)
                # ----------------------------------------
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
                estado_reporte["img_resumen"] = img_bytes_resumen # Guardar para PDF
                imagen_resumen.src_base64 = base64.b64encode(img_bytes_resumen).decode('utf-8')
            else:
                imagen_resumen.src_base64 = "" # Limpiar si no hay datos
                print("Advertencia: Datos de resumen general incompletos.")


            # 2. Gráfico de Productos Más Vendidos
            if datos.get('productos_mas_vendidos'):
                nombres_pv = [p['nombre'] for p in datos['productos_mas_vendidos']]
                cantidades_pv = [p['cantidad'] for p in datos['productos_mas_vendidos']]
                fig_pv = px.bar(x=nombres_pv, y=cantidades_pv, orientation='v', title='Productos Más Vendidos (General)', labels={'x': 'Producto', 'y': 'Cantidad'})
                fig_pv.update_layout(height=300)
                # Convertir a bytes y actualizar imagen
                img_bytes_pv = fig_pv.to_image(format="png", width=600, height=300, scale=1)
                estado_reporte["img_productos"] = img_bytes_pv # Guardar para PDF
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
                estado_reporte["img_horas"] = img_bytes_hora # Guardar para PDF
                imagen_ventas_hora.src_base64 = base64.b64encode(img_bytes_hora).decode('utf-8')
            else:
                imagen_ventas_hora.src_base64 = "" # Limpiar si no hay datos


            # --- GENERAR GRÁFICO DE EFICIENCIA DE COCINA ---
            if detalle_pedidos_cocina:
                # Extraer IDs de pedido y tiempos
                ids_pedidos = [p['id'] for p in detalle_pedidos_cocina]
                tiempos_cocina = [p['tiempo'] for p in detalle_pedidos_cocina]
                # Crear gráfico de barras (o scatter) de tiempos por pedido
                # Truncar IDs si son muy largos para la visualización
                labels_pedidos = [f"Pedido {p['id']}" for p in detalle_pedidos_cocina]
                fig_eficiencia = px.bar(x=labels_pedidos, y=tiempos_cocina, orientation='v', title=f'Tiempos de Cocina - {tipo} ({fecha_str})', labels={'x': 'Pedido', 'y': 'Tiempo (min)'})
                fig_eficiencia.add_hline(y=promedio_cocina_min, line_dash="dash", line_color="red", annotation_text=f"Promedio: {promedio_cocina_min:.2f} min")
                fig_eficiencia.update_layout(height=300)
                # Convertir a bytes y actualizar imagen
                img_bytes_eficiencia = fig_eficiencia.to_image(format="png", width=600, height=300, scale=1)
                estado_reporte["img_eficiencia"] = img_bytes_eficiencia # Guardar para PDF
                imagen_eficiencia_cocina.src_base64 = base64.b64encode(img_bytes_eficiencia).decode('utf-8')
                texto_eficiencia_cocina.value = f"Promedio: {promedio_cocina_min:.2f} minutos"
            else:
                imagen_eficiencia_cocina.src_base64 = "" # Limpiar si no hay datos
                texto_eficiencia_cocina.value = "No hay pedidos completados en cocina para este periodo."

            # --- FIN GENERAR GRÁFICO DE EFICIENCIA DE COCINA ---


            # --- ACTUALIZAR ANÁLISIS DE PRODUCTOS ---
            # Calcular rango de fechas para el análisis (similar al reporte general)
            start_date_analisis = None
            end_date_analisis = None

            if tipo == "Diario":
                start_date_analisis = fecha.strftime("%Y-%m-%d")
                end_date_analisis = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
            elif tipo == "Semanal":
                # Calcular lunes de la semana
                start_of_week = fecha - timedelta(days=fecha.weekday())
                start_date_analisis = start_of_week.strftime("%Y-%m-%d")
                end_date_analisis = (start_of_week + timedelta(days=6)).strftime("%Y-%m-%d")
            elif tipo == "Mensual":
                # Primer día del mes
                start_date_analisis = fecha.replace(day=1).strftime("%Y-%m-%d")
                # Último día del mes
                if fecha.month == 12:
                    end_date_analisis = fecha.replace(day=31).strftime("%Y-%m-%d")
                else:
                    # Primer día del siguiente mes - 1 día
                    next_month = fecha.replace(day=1) + timedelta(days=32)
                    end_date_analisis = (next_month.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
            elif tipo == "Anual":
                start_date_analisis = fecha.replace(month=1, day=1).strftime("%Y-%m-%d")
                end_date_analisis = fecha.replace(month=12, day=31).strftime("%Y-%m-%d")
            else:
                # Default a diario si el tipo no coincide
                start_date_analisis = fecha.strftime("%Y-%m-%d")
                end_date_analisis = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
            # ================================================

            # Limpiar contenedor de análisis (solo texto)
            controles_analisis_texto = []
            controles_analisis_texto.append(ft.Text(f"Análisis de Productos - {tipo} ({start_date_analisis} a {end_date_analisis})", size=20, weight=ft.FontWeight.BOLD))
            controles_analisis_texto.append(ft.Divider())

            try:
                # Obtener datos del backend para el análisis
                datos_analisis = backend_service.obtener_analisis_productos(start_date=start_date_analisis, end_date=end_date_analisis)

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
                fig_am = px.bar(x=nombres_am, y=cantidades_am, orientation='v', title='Análisis - Más Vendidos', labels={'x': 'Producto', 'y': 'Cantidad'})
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
                fig_anm = px.bar(x=nombres_anm, y=cantidades_anm, orientation='v', title='Análisis - Menos Vendidos', labels={'x': 'Producto', 'y': 'Cantidad'})
                fig_anm.update_layout(height=300)
                # Convertir a bytes y actualizar imagen
                img_bytes_anm = fig_anm.to_image(format="png", width=600, height=300, scale=1)
                imagen_analisis_menos.src_base64 = base64.b64encode(img_bytes_anm).decode('utf-8')
            else:
                imagen_analisis_menos.src_base64 = "" # Limpiar si no hay datos


            # Reconstruir contenedor_reporte con DASHBOARD + texto y gráficos (imagen)
            contenedor_reporte.content.controls = [
                dashboard_ejecutivo,  # AÑADIR DASHBOARD AL INICIO
                ft.Divider(),
            ] + controles_texto + [
                ft.Text("Gráfico Resumen General", size=16, weight=ft.FontWeight.BOLD),
                imagen_resumen,
                ft.Text("Gráfico Productos Más Vendidos", size=16, weight=ft.FontWeight.BOLD),
                imagen_productos_vendidos,
                ft.Text("Gráfico Ventas por Hora", size=16, weight=ft.FontWeight.BOLD),
                imagen_ventas_hora,
                # --- AÑADIR CONTENEDOR DE EFICIENCIA ---
                contenedor_eficiencia_cocina
                # --- FIN AÑADIR ---
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
            # Limpiar imagen de eficiencia
            imagen_eficiencia_cocina.src_base64 = ""
            texto_eficiencia_cocina.value = "Error al cargar datos de eficiencia."
            
            vista.update()  # ← Actualizar toda la vista
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
            ft.ElevatedButton(
                "Exportar a PDF",
                icon=ft.Icons.PICTURE_AS_PDF,
                on_click=exportar_pdf_click,
                style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
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