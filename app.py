# === APP.PY ===
# Módulo principal de la interfaz gráfica del sistema de restaurante usando Flet.

import flet as ft
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
import threading
import time
import requests
import winsound
import time as time_module


# IMPORTAR LAS NUEVAS CLASES DE INVENTARIO
from inventario_view import crear_vista_inventario
from inventario_service import InventoryService
from recetas_view import crear_vista_recetas
from configuraciones_view import crear_vista_configuraciones


# === FUNCIÓN: reproducir_sonido_pedido ===
# Reproduce una melodía simple cuando se confirma un pedido.

def reproducir_sonido_pedido():
    try:
        # Melodía: Do - Mi - Sol
        tones = [523, 659, 784]  # Hz
        for tone in tones:
            winsound.Beep(tone, 200)  # 200 ms por nota
            time_module.sleep(0.05)
    except Exception as e:
        print(f"Error al reproducir sonido: {e}")

# === FUNCIÓN: generar_resumen_pedido ===
# Genera un texto resumen del pedido actual con items y total.

def generar_resumen_pedido(pedido):
    if not pedido.get("items"):
        return "Sin items."
    
    total = sum(item["precio"] for item in pedido["items"])
    items_str = "\n".join(f"- {item['nombre']} (${item['precio']:.2f})" for item in pedido["items"])
    titulo = obtener_titulo_pedido(pedido)
    return f"[{titulo}]\n{items_str}\nTotal: ${total:.2f}"

# === FUNCIÓN: obtener_titulo_pedido ===
# Genera el título del pedido dependiendo si es de mesa o app.

def obtener_titulo_pedido(pedido):
    if pedido.get("mesa_numero") == 99 and pedido.get("numero_app"):
        return f"Digital #{pedido['numero_app']:03d}"  # ✅ CAMBIAR A "Digital"
    else:
        return f"Mesa {pedido['mesa_numero']}"

# === FUNCIÓN: crear_selector_item ===
# Crea un selector con dropdowns para filtrar y elegir items del menú.

def crear_selector_item(menu):
    tipos = list(set(item["tipo"] for item in menu))
    tipos.sort()

    tipo_dropdown = ft.Dropdown(
        label="Tipo de item",
        options=[ft.dropdown.Option(tipo) for tipo in tipos],
        value=tipos[0] if tipos else "Entradas",
        width=200,
    )

    search_field = ft.TextField(
        label="Buscar ítem...",
        prefix_icon=ft.Icons.SEARCH,
        width=200,
        hint_text="Escribe para filtrar..."
    )

    items_dropdown = ft.Dropdown(
        label="Seleccionar item",
        width=200,
    )

    def filtrar_items(e):
        query = search_field.value.lower().strip() if search_field.value else ""
        tipo_actual = tipo_dropdown.value

        if query:
            items_filtrados = [item for item in menu if query in item["nombre"].lower()]
        else:
            items_filtrados = [item for item in menu if item["tipo"] == tipo_actual]

        items_dropdown.options = [ft.dropdown.Option(item["nombre"]) for item in items_filtrados]
        items_dropdown.value = None
        if e and e.page:
            e.page.update()

    def actualizar_items(e):
        filtrar_items(e)

    tipo_dropdown.on_change = actualizar_items
    search_field.on_change = filtrar_items

    actualizar_items(None)

    container = ft.Column([
        tipo_dropdown,
        search_field,
        items_dropdown
    ], spacing=10)

    container.tipo_dropdown = tipo_dropdown
    container.search_field = search_field
    container.items_dropdown = items_dropdown
    
    def get_selected_item():
        tipo = tipo_dropdown.value
        nombre = items_dropdown.value
        if tipo and nombre:
            for item in menu:
                if item["nombre"] == nombre and item["tipo"] == tipo:
                    return item
        return None
    
    container.get_selected_item = get_selected_item
    return container

# === FUNCIÓN: crear_mesas_grid ===
# Genera una cuadrícula visual de mesas físicas y una mesa virtual para pedidos app.

def crear_mesas_grid(backend_service, on_select):
    try:
        # Obtener el estado real de las mesas del backend
        mesas_backend = backend_service.obtener_mesas()
        
        # Si el backend no tiene mesas, usar valores por defecto
        if not mesas_backend:
            mesas_fisicas = [
                {"numero": 1, "capacidad": 2, "ocupada": False},
                {"numero": 2, "capacidad": 2, "ocupada": False},
                {"numero": 3, "capacidad": 4, "ocupada": False},
                {"numero": 4, "capacidad": 4, "ocupada": False},
                {"numero": 5, "capacidad": 6, "ocupada": False},
                {"numero": 6, "capacidad": 6, "ocupada": False},
            ]
        else:
            mesas_fisicas = mesas_backend
    except Exception as e:
        print(f"Error al obtener mesas del backend: {e}")
        # Usar valores por defecto si hay error
        mesas_fisicas = [
            {"numero": 1, "capacidad": 2, "ocupada": False},
            {"numero": 2, "capacidad": 2, "ocupada": False},
            {"numero": 3, "capacidad": 4, "ocupada": False},
            {"numero": 4, "capacidad": 4, "ocupada": False},
            {"numero": 5, "capacidad": 6, "ocupada": False},
            {"numero": 6, "capacidad": 6, "ocupada": False},
        ]
    
    grid = ft.GridView(
        expand=1,
        runs_count=2,
        max_extent=200,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
        padding=10,
    )

    for mesa in mesas_fisicas:
        if mesa["numero"] == 99:
            continue
            
        color = ft.Colors.GREEN_700 if not mesa["ocupada"] else ft.Colors.RED_700
        estado = "LIBRE" if not mesa["ocupada"] else "OCUPADA"

        grid.controls.append(
            ft.Container(
                key=f"mesa-{mesa['numero']}",
                bgcolor=color,
                border_radius=10,
                padding=15,
                ink=True,
                on_click=lambda e, num=mesa['numero']: on_select(num),
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.TABLE_RESTAURANT, color=ft.Colors.AMBER_400),
                                ft.Text(f"Mesa {mesa['numero']}", size=16, weight=ft.FontWeight.BOLD),
                            ]
                        ),
                        ft.Text(f"Capacidad: {mesa['capacidad']}", size=12),
                        ft.Text(estado, size=14, weight=ft.FontWeight.BOLD)
                    ]
                )
            )
        )

    # Mesa virtual
    contenido_mesa_virtual = ft.Column(
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.MOBILE_FRIENDLY, color=ft.Colors.AMBER_400),
                    ft.Text("Digital", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),  # ✅ CAMBIAR A "Digital"
                ]
            ),
            ft.Text("📱 Pedido por Digital", size=12, color=ft.Colors.WHITE),  # ✅ CAMBIAR A "Digital"
            ft.Text("Siempre disponible", size=10, color=ft.Colors.WHITE),
        ]
    )

    grid.controls.append(
        ft.Container(
            key="mesa-99",
            bgcolor=ft.Colors.BLUE_700,
            border_radius=10,
            padding=15,
            ink=True,
            on_click=lambda e: on_select(99),
            width=200,
            height=120,
            content=contenido_mesa_virtual
        )
    )

    return grid

# === FUNCIÓN: crear_panel_gestion ===
# Crea el panel lateral para gestionar pedidos de una mesa seleccionada.

def crear_panel_gestion(backend_service, menu, on_update_ui, page):
    estado = {"mesa_seleccionada": None, "pedido_actual": None}

    mesa_info = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    tamaño_grupo_input = ft.TextField(
        label="Tamaño del grupo",
        input_filter=ft.NumbersOnlyInputFilter(),
        prefix_icon=ft.Icons.PEOPLE
    )

    # Campo de texto para la nota
    nota_pedido = ft.TextField(
        label="Notas del pedido",
        multiline=True,
        max_lines=3,
        hint_text="Ej: Sin cebolla, sin salsa, etc.",
        width=400
    )

    selector_item = crear_selector_item(menu)

    asignar_btn = ft.ElevatedButton(
        text="Asignar Cliente",
        disabled=True,
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
    )

    agregar_item_btn = ft.ElevatedButton(
        text="Agregar Item",
        disabled=True,
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
    )

    eliminar_ultimo_btn = ft.ElevatedButton(
        text="Eliminar último ítem",
        disabled=True,
        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
    )

    # Nuevo botón: Confirmar Pedido
    confirmar_pedido_btn = ft.ElevatedButton(
        text="Confirmar Pedido",
        disabled=True,
        style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE)
    )

    

    resumen_pedido = ft.Text("", size=14)

    def actualizar_estado_botones():
        mesa_seleccionada = estado["mesa_seleccionada"]
        pedido_actual = estado["pedido_actual"]
        
        if not mesa_seleccionada:
            asignar_btn.disabled = True
            agregar_item_btn.disabled = True
            eliminar_ultimo_btn.disabled = True
            confirmar_pedido_btn.disabled = True
            
            return

        if mesa_seleccionada.get("numero") == 99:
            asignar_btn.disabled = pedido_actual is not None
            agregar_item_btn.disabled = pedido_actual is None
            eliminar_ultimo_btn.disabled = pedido_actual is None or not pedido_actual.get("items", [])
            confirmar_pedido_btn.disabled = pedido_actual is None or not pedido_actual.get("items", [])
            
        else:
            asignar_btn.disabled = mesa_seleccionada.get("ocupada", False)
            agregar_item_btn.disabled = pedido_actual is None
            eliminar_ultimo_btn.disabled = pedido_actual is None or not pedido_actual.get("items", [])
            confirmar_pedido_btn.disabled = pedido_actual is None or not pedido_actual.get("items", [])
            

        page.update()

    def seleccionar_mesa_interna(numero_mesa):
        try:
            mesas = backend_service.obtener_mesas()
            mesa_seleccionada = next((m for m in mesas if m["numero"] == numero_mesa), None)
            estado["mesa_seleccionada"] = mesa_seleccionada
            estado["pedido_actual"] = None
            
            if not mesa_seleccionada:
                return

            if mesa_seleccionada["numero"] == 99:
                mesa_info.value = "Digital - Pedidos por aplicación móvil"  # ✅ CAMBIAR A "Digital"
            else:
                mesa_info.value = f"Mesa {mesa_seleccionada['numero']} - Capacidad: {mesa_seleccionada['capacidad']} personas"

            resumen_pedido.value = ""
            nota_pedido.value = ""
            actualizar_estado_botones()
            
        except Exception as e:
            pass

    def asignar_cliente(e):
        mesa_seleccionada = estado["mesa_seleccionada"]
        if not mesa_seleccionada:
            return

        try:
            # ✅ CREAR PEDIDO EN MEMORIA (NO EN BASE DE DATOS AÚN)
            nuevo_pedido = {
                "id": None,  # Aún no tiene ID
                "mesa_numero": mesa_seleccionada["numero"],
                "items": [],
                "estado": "Tomando pedido",  # ✅ ESTADO TEMPORAL
                "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "numero_app": None,
                "notas": nota_pedido.value
            }

            estado["pedido_actual"] = nuevo_pedido
            resumen_pedido.value = ""
            on_update_ui()
            actualizar_estado_botones()
            
        except Exception as ex:
            print(f"Error asignar cliente: {ex}")

    def agregar_item_pedido(e):
        mesa_seleccionada = estado["mesa_seleccionada"]
        pedido_actual = estado["pedido_actual"]
        
        if not mesa_seleccionada or not pedido_actual:
            return

        item = selector_item.get_selected_item()
        if not item:
            return

        try:
            # ✅ SOLO ACTUALIZAR EN MEMORIA SI AÚN NO TIENE ID
            if pedido_actual["id"] is None:
                items_actuales = pedido_actual.get("items", [])
                items_actuales.append({
                    "nombre": item["nombre"],
                    "precio": item["precio"],
                    "tipo": item["tipo"],
                    "cantidad": 1
                })
                pedido_actual["items"] = items_actuales
                estado["pedido_actual"] = pedido_actual
            else:
                # ✅ SI YA TIENE ID, ACTUALIZAR EN LA BASE DE DATOS
                items_actuales = pedido_actual.get("items", [])
                items_actuales.append({
                    "nombre": item["nombre"],
                    "precio": item["precio"],
                    "tipo": item["tipo"],
                    "cantidad": 1
                })
                
                # Actualizar el pedido en el backend
                resultado = backend_service.actualizar_pedido(
                    pedido_actual["id"],
                    pedido_actual["mesa_numero"],
                    items_actuales,
                    pedido_actual["estado"],
                    pedido_actual.get("notas", "")
                )
                
                # Actualizar el pedido localmente
                pedido_actual["items"] = items_actuales
                estado["pedido_actual"] = pedido_actual
                
            # Actualizar resumen
            resumen = generar_resumen_pedido(pedido_actual)
            resumen_pedido.value = resumen
            on_update_ui()
            actualizar_estado_botones()
            
        except Exception as ex:
            print(f"Error al agregar ítem: {ex}")

    def eliminar_ultimo_item(e):
        pedido_actual = estado["pedido_actual"]
        if not pedido_actual:
            return

        try:
            backend_service.eliminar_ultimo_item(pedido_actual["id"])
            
            pedidos_activos = backend_service.obtener_pedidos_activos()
            pedido_actualizado = next((p for p in pedidos_activos if p["id"] == pedido_actual["id"]), None)
            
            if pedido_actualizado:
                estado["pedido_actual"] = pedido_actualizado
                resumen = generar_resumen_pedido(pedido_actualizado)
                resumen_pedido.value = resumen
            else:
                resumen_pedido.value = "Sin items."
                estado["pedido_actual"] = None
                
            on_update_ui()
            actualizar_estado_botones()
            
        except Exception as ex:
            print(f"Error al eliminar ítem: {ex}")

    def confirmar_pedido(e):
        pedido_actual = estado["pedido_actual"]
        if not pedido_actual:
            return

        if not pedido_actual.get("items"):
            return  # ✅ No confirmar si no tiene ítems

        try:
            nota_a_guardar = nota_pedido.value.strip() if nota_pedido.value else ""  # ✅ ASEGURAR QUE NO SEA None

            if pedido_actual["id"] is None:
                # ✅ ES UN NUEVO PEDIDO, CREARLO EN LA BASE DE DATOS
                nuevo_pedido = backend_service.crear_pedido(
                    pedido_actual["mesa_numero"],
                    pedido_actual["items"],
                    "Pendiente",  # ✅ ESTADO REAL
                    nota_a_guardar  # ✅ ENVIAR NOTA
                )
                estado["pedido_actual"] = nuevo_pedido
            else:
                # ✅ ACTUALIZAR UN PEDIDO EXISTENTE
                backend_service.actualizar_pedido(
                    pedido_actual["id"],
                    pedido_actual["mesa_numero"],
                    pedido_actual["items"],
                    "Pendiente",
                    nota_a_guardar  # ✅ ENVIAR NOTA
                )

            on_update_ui()  # ✅ ACTUALIZA LAS OTRAS PESTAÑAS

            # Reproducir sonido en un hilo separado para no bloquear la UI
            threading.Thread(target=reproducir_sonido_pedido, daemon=True).start()

        except Exception as ex:
            print(f"Error al confirmar pedido: {ex}")

    
    asignar_btn.on_click = asignar_cliente
    agregar_item_btn.on_click = agregar_item_pedido
    eliminar_ultimo_btn.on_click = eliminar_ultimo_item
    confirmar_pedido_btn.on_click = confirmar_pedido
    

    panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=mesa_info,
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    padding=10,
                    border_radius=10,
                ),
                ft.Container(height=20),
                tamaño_grupo_input,
                asignar_btn,
                ft.Divider(),
                nota_pedido,
                ft.Divider(),
                selector_item,
                agregar_item_btn,
                eliminar_ultimo_btn,
                confirmar_pedido_btn,
                ft.Divider(),
                ft.Divider(),
                ft.Text("Resumen del pedido", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=resumen_pedido,
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    padding=10,
                    border_radius=10,
                )
            ],
            spacing=10,
            expand=True,
        ),
        padding=20,
        expand=True
    )

    panel.seleccionar_mesa = seleccionar_mesa_interna
    return panel

# === FUNCIÓN: crear_vista_cocina ===
# Vista de cocina para ver y gestionar pedidos activos.

def crear_vista_cocina(backend_service, on_update_ui, page):
    lista_pedidos = ft.ListView(
        expand=1,
        spacing=10,
        padding=20,
        auto_scroll=True,
    )

    def actualizar():
        try:
            pedidos = backend_service.obtener_pedidos_activos()
            lista_pedidos.controls.clear()
            for pedido in pedidos:
                # ✅ SOLO MOSTRAR SI ESTÁ PENDIENTE O EN PREPARACIÓN
                if pedido.get("estado") in ["Pendiente", "En preparacion"] and pedido.get("items"):
                    lista_pedidos.controls.append(crear_item_pedido_cocina(pedido, backend_service, on_update_ui))
            page.update()
        except Exception as e:
            print(f"Error al cargar pedidos: {e}")

    def crear_item_pedido_cocina(pedido, backend_service, on_update_ui):
        def cambiar_estado(e, p, nuevo_estado):
            try:
                backend_service.actualizar_estado_pedido(p["id"], nuevo_estado)
                on_update_ui()  # ✅ ACTUALIZA AMBAS VISTAS
            except Exception as ex:
                print(f"Error al cambiar estado: {ex}")

        def eliminar_pedido_click(e):
            try:
                # ✅ ELIMINAR EL PEDIDO DE LA BASE DE DATOS
                backend_service.eliminar_pedido(pedido["id"])
                on_update_ui()  # ✅ ACTUALIZAR INTERFAZ
            except Exception as ex:
                print(f"Error al eliminar pedido: {ex}")

        origen = f"{obtener_titulo_pedido(pedido)} - {pedido.get('fecha_hora', 'Sin fecha')}"
        nota = f"Notas: {pedido.get('notas', 'Ninguna')}"
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(origen, size=20, weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        on_click=eliminar_pedido_click,
                        tooltip="Eliminar pedido",
                        icon_color=ft.Colors.RED_700
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(generar_resumen_pedido(pedido)),
                ft.Text(nota, color=ft.Colors.YELLOW_200),
                ft.Row([
                    ft.ElevatedButton(
                        "En preparacion",
                        on_click=lambda e, p=pedido: cambiar_estado(e, p, "En preparacion"),
                        disabled=pedido.get("estado") != "Pendiente",
                        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE)
                    ),
                    ft.ElevatedButton(
                        "Listo",
                        on_click=lambda e, p=pedido: cambiar_estado(e, p, "Listo"),
                        disabled=pedido.get("estado") != "En preparacion",
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
                    ),
                ]),
                ft.Text(f"Estado: {pedido.get('estado', 'Pendiente')}", color=ft.Colors.BLUE_200)
            ]),
            bgcolor=ft.Colors.BLUE_GREY_900,
            padding=10,
            border_radius=10,
        )

    vista = ft.Container(
        content=ft.Column([
            ft.Text("Pedidos en Cocina", size=20, weight=ft.FontWeight.BOLD),
            lista_pedidos
        ]),
        padding=20,
        expand=True
    )

    vista.actualizar = actualizar
    return vista

# === FUNCIÓN: crear_vista_caja ===
# Vista de caja para gestionar pagos y eliminar pedidos.

def crear_vista_caja(backend_service, on_update_ui, page):
    lista_cuentas = ft.ListView(
        expand=1,
        spacing=10,
        padding=20,
        auto_scroll=True,
    )

    def actualizar():
        try:
            pedidos = backend_service.obtener_pedidos_activos()
            lista_cuentas.controls.clear()
            for pedido in pedidos:
                # ✅ MOSTRAR SI ESTÁ LISTO, ENTREGADO O PAGADO
                if pedido.get("estado") in ["Listo", "Entregado", "Pagado"] and pedido.get("items"):
                    item = crear_item_cuenta(pedido, backend_service, on_update_ui, page)
                    if item:
                        lista_cuentas.controls.append(item)
            page.update()
        except Exception as e:
            print(f"Error al cargar pedidos: {e}")

    def crear_item_cuenta(pedido, backend_service, on_update_ui, page):
        total_pedido = sum(item["precio"] for item in pedido["items"])

        # ✅ CAMPOS PARA PAGO Y CAMBIO
        pago_cliente = ft.TextField(
            label="Con cuánto paga",
            input_filter=ft.NumbersOnlyInputFilter(),
            width=200
        )
        cambio_text = ft.Text("Cambio: $0.00", size=14, weight=ft.FontWeight.BOLD)

        # ✅ DROPDOWN PARA MÉTODO DE PAGO
        metodo_pago = ft.Dropdown(
            label="Método de pago",
            options=[
                ft.dropdown.Option("Efectivo"),
                ft.dropdown.Option("Tarjeta"),
                ft.dropdown.Option("QR"),
            ],
            value="Efectivo",  # Valor por defecto
            width=200
        )

        def procesar_pago(e):
            try:
                pago = float(pago_cliente.value)
                if pago < total_pedido:
                    return
                cambio = pago - total_pedido
                cambio_text.value = f"Cambio: ${cambio:.2f}"
                page.update()
            except ValueError:
                pass

        def terminar_pedido(e):
            try:
                # ✅ ACTUALIZAR ESTADO A "Pagado"
                backend_service.actualizar_estado_pedido(pedido["id"], "Pagado")
                on_update_ui()
            except Exception as ex:
                print(f"Error al terminar pedido: {ex}")

        def eliminar_pedido(e):
            try:
                # Eliminar pedido del backend
                backend_service.eliminar_pedido(pedido["id"])
                on_update_ui()
            except Exception as ex:
                print(f"Error al eliminar pedido: {ex}")

        origen = f"{obtener_titulo_pedido(pedido)} - {pedido.get('fecha_hora', 'Sin fecha')}"
        cliente_id = "Cliente App"

        return ft.Container(
            content=ft.Column([
                ft.Text(origen, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Cliente {cliente_id}"),
                ft.Text(f"Estado: {pedido.get('estado', 'Pendiente')}", color=ft.Colors.BLUE_200),
                ft.Text(generar_resumen_pedido(pedido)),
                ft.Text(f"Total: ${total_pedido:.2f}", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    pago_cliente,
                    ft.ElevatedButton(
                        "Calcular cambio",
                        on_click=procesar_pago,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE)
                    )
                ]),
                cambio_text,
                ft.Row([
                    metodo_pago,  # ✅ DROPDOWN DE MÉTODO DE PAGO
                ]),
                ft.Row([
                    ft.ElevatedButton(
                        "Terminar pedido",
                        on_click=terminar_pedido,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
                    ),
                    ft.ElevatedButton(
                        "Eliminar pedido",
                        on_click=eliminar_pedido,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_800, color=ft.Colors.WHITE),
                        tooltip="Eliminar pedido accidental"
                    )
                ])
            ]),
            bgcolor=ft.Colors.BLUE_GREY_900,
            padding=10,
            border_radius=10
        )

    vista = ft.Container(
        content=ft.Column([
            ft.Text("Cuentas activas", size=24, weight=ft.FontWeight.BOLD),
            lista_cuentas
        ]),
        expand=True
    )

    vista.actualizar = actualizar
    return vista

# === FUNCIÓN: crear_vista_admin ===
# Vista de administración para gestionar menú y clientes.

def crear_vista_admin(backend_service, menu, on_update_ui, page):
    tipos = list(set(item["tipo"] for item in menu))
    tipos.sort()

    tipo_item_admin = ft.Dropdown(
        label="Tipo de item (Agregar)",
        options=[ft.dropdown.Option(tipo) for tipo in tipos],
        value=tipos[0] if tipos else "Entradas",
        width=250,
    )

    nombre_item = ft.TextField(label="Nombre de item", width=250)
    precio_item = ft.TextField(label="Precio", width=250)

    tipo_item_eliminar = ft.Dropdown(
        label="Tipo item (Eliminar)",
        options=[ft.dropdown.Option(tipo) for tipo in tipos],
        value=tipos[0] if tipos else "Entradas",
        width=250,
    )

    item_eliminar = ft.Dropdown(label="Seleccionar item a eliminar", width=300)

    def actualizar_items_eliminar(e):
        tipo = tipo_item_eliminar.value
        items = [item for item in menu if item["tipo"] == tipo]
        item_eliminar.options = [ft.dropdown.Option(item["nombre"]) for item in items]
        item_eliminar.value = None
        page.update()

    tipo_item_eliminar.on_change = actualizar_items_eliminar
    actualizar_items_eliminar(None)

    def agregar_item(e):
        tipo = tipo_item_admin.value
        nombre = (nombre_item.value or "").strip()
        texto_precio = (precio_item.value or "").strip()

        if not tipo or not nombre or not texto_precio:
            return

        texto_precio = texto_precio.replace(",", ".")
        try:
            precio = float(texto_precio)
        except ValueError:
            return

        if precio <= 0:
            return

        try:
            # Usar el nuevo método del backend
            backend_service.agregar_item_menu(nombre, precio, tipo)
            on_update_ui()
        except Exception as ex:
            print(f"Error al agregar item: {ex}")

    def eliminar_item(e):
        tipo = tipo_item_eliminar.value
        nombre = item_eliminar.value
        if not tipo or not nombre:
            return

        try:
            # Usar el nuevo método del backend
            backend_service.eliminar_item_menu(nombre, tipo)
            on_update_ui()
        except Exception as ex:
            print(f"Error al eliminar item: {ex}")

    # Campos para clientes
    nombre_cliente = ft.TextField(label="Nombre", width=300)
    domicilio_cliente = ft.TextField(label="Domicilio", width=300)
    celular_cliente = ft.TextField(
        label="Celular",
        width=300,
        input_filter=ft.NumbersOnlyInputFilter(),
        prefix_icon=ft.Icons.PHONE
    )

    # ✅ LISTA DE CLIENTES - CON ESPACIO MÁXIMO HORIZONTAL Y VERTICAL
    lista_clientes = ft.ListView(
        expand=True,  # ✅ EXPANDIR PARA OCUPAR TODO EL ESPACIO
        spacing=10,
        padding=20,
        auto_scroll=True,
    )

    def actualizar_lista_clientes():
        try:
            clientes = backend_service.obtener_clientes()
            lista_clientes.controls.clear()
            for cliente in clientes:
                cliente_row = ft.Container(
                    content=ft.Column([
                        ft.Text(f"{cliente['nombre']}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Domicilio: {cliente['domicilio']}", size=14),
                        ft.Text(f"Celular: {cliente['celular']}", size=14),
                        ft.Text(f"Registrado: {cliente['fecha_registro']}", size=12, color=ft.Colors.GREY_500),
                        ft.ElevatedButton(
                            "Eliminar",
                            on_click=lambda e, id=cliente['id']: eliminar_cliente_click(id),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                        )
                    ]),
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    padding=10,
                    border_radius=10
                )
                lista_clientes.controls.append(cliente_row)
            page.update()
        except Exception as e:
            print(f"Error al cargar clientes: {e}")

    def agregar_cliente_click(e):
        nombre = nombre_cliente.value
        domicilio = domicilio_cliente.value
        celular = celular_cliente.value

        if not nombre or not domicilio or not celular:
            return

        try:
            backend_service.agregar_cliente(nombre, domicilio, celular)
            nombre_cliente.value = ""
            domicilio_cliente.value = ""
            celular_cliente.value = ""
            actualizar_lista_clientes()
        except Exception as ex:
            print(f"Error al agregar cliente: {ex}")

    def eliminar_cliente_click(cliente_id: int):
        try:
            backend_service.eliminar_cliente(cliente_id)
            actualizar_lista_clientes()
        except Exception as ex:
            print(f"Error al eliminar cliente: {ex}")

    vista = ft.Container(
        content=ft.Column([
            # Sección de menú
            ft.Text("Agregar item al menú", size=20, weight=ft.FontWeight.BOLD),
            tipo_item_admin,
            nombre_item,
            precio_item,
            ft.ElevatedButton(
                text="Agregar item",
                on_click=agregar_item,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            ),
            ft.Divider(),
            ft.Text("Eliminar item del menú", size=20, weight=ft.FontWeight.BOLD),
            tipo_item_eliminar,
            item_eliminar,
            ft.ElevatedButton(
                text="Eliminar item",
                on_click=eliminar_item,
                style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
            ),
            ft.Divider(),
            # Sección de clientes
            ft.Text("Agregar Cliente", size=20, weight=ft.FontWeight.BOLD),
            nombre_cliente,
            domicilio_cliente,
            celular_cliente,
            ft.ElevatedButton(
                "Agregar Cliente",
                on_click=agregar_cliente_click,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            ),
            ft.Divider(),
            ft.Text("Clientes Registrados", size=20, weight=ft.FontWeight.BOLD),
            # ✅ SECCIÓN SEPARADA PARA CLIENTES REGISTRADOS - OCUPA TODO EL ANCHO
            ft.Container(
                content=lista_clientes,
                expand=True,  # ✅ CONTAINER EXPANDIDO
                height=500,  # ✅ ALTURA AMPLIA
                bgcolor=ft.Colors.BLUE_GREY_900,  # ✅ FONDO PARA VER MEJOR
                padding=10,
                border_radius=10,
            )
        ], expand=True, scroll="auto"),  # ✅ SCROLL VERTICAL EN LA COLUMNA
        padding=20,
        bgcolor=ft.Colors.BLUE_GREY_900,
        expand=True  # ✅ CONTAINER PRINCIPAL EXPANDIDO
    )

    vista.actualizar_lista_clientes = actualizar_lista_clientes
    return vista

# === CLASE: RestauranteGUI ===
# Clase principal que maneja la interfaz gráfica y los estados del sistema.

class RestauranteGUI:
    def __init__(self):
        from backend_service import BackendService
        from recetas_service import RecetasService  # ✅ IMPORTAR SERVICIO DE RECETAS
        from configuraciones_service import ConfiguracionesService  # ✅ IMPORTAR SERVICIO DE CONFIGURACIONES
        self.backend_service = BackendService()
        self.inventory_service = InventoryService()
        self.recetas_service = RecetasService()  # ✅ INICIALIZAR SERVICIO DE RECETAS
        self.config_service = ConfiguracionesService()  # ✅ INICIALIZAR SERVICIO DE CONFIGURACIONES
        self.page = None
        self.mesas_grid = None
        self.panel_gestion = None
        self.vista_cocina = None
        self.vista_caja = None
        self.vista_admin = None
        self.vista_inventario = None
        self.vista_recetas = None  # ✅ AGREGAR ESTO
        self.vista_configuraciones = None  # ✅ AGREGAR ESTO
        self.menu_cache = None
        

    def main(self, page: ft.Page):
        self.page = page
        page.title = "Sistema Restaurante Profesional"
        page.padding = 0
        page.theme_mode = "dark"

        reloj = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_200)

        def actualizar_reloj():
            reloj.value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            page.update()

        def loop_reloj():
            while True:
                actualizar_reloj()
                time.sleep(1)

        hilo_reloj = threading.Thread(target=loop_reloj, daemon=True)
        hilo_reloj.start()

        try:
            self.menu_cache = self.backend_service.obtener_menu()
        except Exception as e:
            print(f"Error al cargar menú: {e}")
            self.menu_cache = []

        self.mesas_grid = crear_mesas_grid(self.backend_service, self.seleccionar_mesa)
        self.panel_gestion = crear_panel_gestion(self.backend_service, self.menu_cache, self.actualizar_ui_completo, page)
        self.vista_cocina = crear_vista_cocina(self.backend_service, self.actualizar_ui_completo, page)
        self.vista_caja = crear_vista_caja(self.backend_service, self.actualizar_ui_completo, page)
        self.vista_admin = crear_vista_admin(self.backend_service, self.menu_cache, self.actualizar_ui_completo, page)
        self.vista_inventario = crear_vista_inventario(self.inventory_service, self.actualizar_ui_completo, page)
        self.vista_recetas = crear_vista_recetas(self.recetas_service, self.actualizar_ui_completo, page)  # ✅ CREAR VISTA DE RECETAS
        self.vista_configuraciones = crear_vista_configuraciones(self.config_service, self.actualizar_ui_completo, page)  # ✅ CREAR VISTA DE CONFIGURACIONES

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Mesera",
                    icon=ft.Icons.PERSON,
                    content=self.crear_vista_mesera()
                ),
                ft.Tab(
                    text="Cocina",
                    icon=ft.Icons.RESTAURANT,
                    content=self.vista_cocina
                ),
                ft.Tab(
                    text="Caja",
                    icon=ft.Icons.POINT_OF_SALE,
                    content=self.vista_caja
                ),
                ft.Tab(
                    text="Administracion",
                    icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                    content=self.vista_admin
                ),
                ft.Tab(
                    text="Inventario",
                    icon=ft.Icons.INVENTORY_2,
                    content=self.vista_inventario
                ),
                ft.Tab(  # ✅ PESTAÑA DE RECETAS
                    text="Recetas",
                    icon=ft.Icons.BOOK,
                    content=self.vista_recetas
                ),
                ft.Tab(  # ✅ PESTAÑA DE CONFIGURACIONES
                    text="Configuraciones",
                    icon=ft.Icons.SETTINGS,
                    content=self.vista_configuraciones
                ),
            ],
            expand=1
        )

        page.add(
            ft.Stack(
                controls=[
                    tabs,
                    ft.Container(
                        content=reloj,
                        left=20,
                        bottom=50,
                        padding=10,
                        bgcolor=ft.Colors.BLUE_GREY_900,
                        border_radius=8,
                    )
                ],
                expand=True
            )
        )

        # ✅ LLAMAR A on_update_ui() AL INICIO PARA CARGAR DATOS
        self.actualizar_ui_completo()

    def crear_vista_mesera(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("Mesas del restaurante", size=20, weight=ft.FontWeight.BOLD),
                            self.mesas_grid
                        ],
                        expand=True
                    ),
                    ft.VerticalDivider(),
                    ft.Container(
                        width=400,
                        content=self.panel_gestion,
                        expand=True
                    )
                ],
                expand=True
            ),
            expand=True
        )

    def seleccionar_mesa(self, numero_mesa: int):
        if self.panel_gestion:
            self.panel_gestion.seleccionar_mesa(numero_mesa)

    def actualizar_ui_completo(self):
        nuevo_grid = crear_mesas_grid(self.backend_service, self.seleccionar_mesa)
        self.mesas_grid.controls = nuevo_grid.controls
        self.mesas_grid.update()

        if hasattr(self.vista_cocina, 'actualizar'):
            self.vista_cocina.actualizar()
        if hasattr(self.vista_caja, 'actualizar'):
            self.vista_caja.actualizar()
        if hasattr(self.vista_admin, 'actualizar_lista_clientes'):
            self.vista_admin.actualizar_lista_clientes()
        if hasattr(self.vista_inventario, 'actualizar_lista'):
            self.vista_inventario.actualizar_lista()

        self.page.update()

def main():
    app = RestauranteGUI()
    ft.app(target=app.main)

if __name__ == "__main__":
    main()