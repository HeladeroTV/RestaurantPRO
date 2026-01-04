import flet as ft
from typing import List, Dict, Any

def crear_vista_bienvenida(backend_service, on_update_ui, page):
    # --- PESTAÑA 1: MENÚ Y CATEGORÍAS ---
    
    # Variables de estado
    categorias_disponibles = []
    items_categoria_seleccionada = []
    
    # Controles de UI para Categorías
    nueva_categoria_input = ft.TextField(label="Nombre Categoria (Ej: Entradas)", width=300)
    categoria_dropdown = ft.Dropdown(
        label="Seleccionar Categoría",
        width=300,
    )
    
    # Controles de UI para Ítems
    nombre_item_input = ft.TextField(label="Nombre del Platillo", width=250)
    precio_item_input = ft.TextField(
        label="Precio", 
        width=150,
        input_filter=ft.NumbersOnlyInputFilter(),
        prefix_text="$"
    )
    lista_items_container = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, height=300)

    def cargar_datos_menu():
        try:
            menu = backend_service.obtener_menu()
            nonlocal categorias_disponibles
            # Extraer categorías únicas
            categorias_disponibles = sorted(list(set(item["tipo"] for item in menu)))
            
            # Actualizar dropdown
            categoria_dropdown.options = [ft.dropdown.Option(c) for c in categorias_disponibles]
            if not categoria_dropdown.value and categorias_disponibles:
                categoria_dropdown.value = categorias_disponibles[0]
            
            actualizar_lista_items()
            page.update()
        except Exception as e:
            print(f"Error cargando menú: {e}")

    def actualizar_lista_items():
        categoria = categoria_dropdown.value
        if not categoria:
            lista_items_container.controls.clear()
            return

        try:
            menu = backend_service.obtener_menu()
            items = [item for item in menu if item["tipo"] == categoria]
            
            lista_items_container.controls.clear()
            for item in items:
                row = ft.Container(
                    content=ft.Row([
                        ft.Text(f"{item['nombre']}", expand=True),
                        ft.Text(f"${item['precio']:.2f}", weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE, 
                            icon_color=ft.Colors.RED_400,
                            tooltip="Eliminar platillo",
                            on_click=lambda e, nome=item['nombre'], tipo=categoria: eliminar_item_click(nome, tipo)
                        )
                    ]),
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    padding=10,
                    border_radius=5
                )
                lista_items_container.controls.append(row)
            
            page.update()
        except Exception as e:
            print(f"Error actualizando lista items: {e}")

    def agregar_categoria_click(e):
        nueva = nueva_categoria_input.value
        if not nueva: return
        
        # En realidad, una categoría "existe" cuando tiene al menos un item.
        # Pero podemos simular crearla añadiendo un item placeholder o simplemente validando.
        # Para simplificar, añadiremos directamente el primer item a esa nueva categoría.
        # O permitimos añadir tipos al dropdown.
        
        # Estrategia: Añadir al dropdown localmente. Se guardará en DB cuando se añada un item de ese tipo.
        if nueva not in categorias_disponibles:
            categorias_disponibles.append(nueva)
            categoria_dropdown.options.append(ft.dropdown.Option(nueva))
            categoria_dropdown.value = nueva
            nueva_categoria_input.value = ""
            actualizar_lista_items()
            page.update()

    def agregar_item_click(e):
        nombre = nombre_item_input.value
        precio_str = precio_item_input.value
        categoria = categoria_dropdown.value
        
        if not nombre or not precio_str or not categoria:
            # Mostrar error
            page.snack_bar = ft.SnackBar(ft.Text("Todos los campos son obligatorios"), bgcolor=ft.Colors.RED_700)
            page.snack_bar.open = True
            page.update()
            return
            
        try:
            precio = float(precio_str)
            backend_service.agregar_item_menu(nombre, precio, categoria)
            
            nombre_item_input.value = ""
            precio_item_input.value = ""
            
            cargar_datos_menu() # Recargar todo
            page.snack_bar = ft.SnackBar(ft.Text("Platillo agregado"), bgcolor=ft.Colors.GREEN_700)
            page.snack_bar.open = True
            page.update()
            
        except Exception as ex:
            print(f"Error agregando item: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED_700)
            page.snack_bar.open = True
            page.update()

    def eliminar_item_click(nombre, tipo):
        try:
            backend_service.eliminar_item_menu(nombre, tipo)
            cargar_datos_menu()
        except Exception as ex:
            print(f"Error eliminando item: {ex}")

    categoria_dropdown.on_change = lambda e: actualizar_lista_items()

    tab_menu = ft.Container(
        content=ft.Column([
            ft.Text("Gestión de Menú y Categorías", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("1. Selecciona o crea una categoría.", size=14, color=ft.Colors.GREY_400),
            ft.Row([
                categoria_dropdown,
                ft.Text("O crear nueva:", size=14),
                nueva_categoria_input,
                ft.ElevatedButton("Crear", on_click=agregar_categoria_click)
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
            ft.Divider(),
            
            ft.Text("2. Agregar Platillos a la categoría seleccionada.", size=14, color=ft.Colors.GREY_400),
            ft.Row([
                nombre_item_input,
                precio_item_input,
                ft.ElevatedButton("Agregar Platillo", on_click=agregar_item_click, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            ]),
            
            ft.Divider(),
            
            ft.Text("Platillos en esta categoría:", size=16, weight=ft.FontWeight.BOLD),
            lista_items_container
        ]),
        padding=20
    )


    # --- PESTAÑA 2: CONFIGURACIÓN DE MESAS ---
    
    total_mesas_input = ft.TextField(
        label="Número Total de Mesas", 
        width=200, 
        value="6",
        input_filter=ft.NumbersOnlyInputFilter()
    )
    
    config_mesas_container = ft.Column(scroll=ft.ScrollMode.AUTO, height=400)
    mesas_inputs = [] # Lista de Refs o controles para leer valores despues

    def generar_inputs_mesas(e):
        try:
            total = int(total_mesas_input.value)
            config_mesas_container.controls.clear()
            mesas_inputs.clear()
            
            for i in range(1, total + 1):
                # Valor por defecto capaicdad: intentar mantener si ya existe, o 4
                capacidad_defecto = "4"
                if i <= 2: capacidad_defecto = "2" # Mesas pequeñas habituales
                elif i >= 5: capacidad_defecto = "6" # Mesas grandes
                
                input_capacidad = ft.TextField(
                    label=f"Capacidad Mesa {i}",
                    value=capacidad_defecto,
                    width=150,
                    input_filter=ft.NumbersOnlyInputFilter()
                )
                mesas_inputs.append({"numero": i, "input": input_capacidad})
                
                fila = ft.Row([
                    ft.Text(f"Mesa {i}:", weight=ft.FontWeight.BOLD, width=80),
                    input_capacidad,
                    ft.Text("personas")
                ])
                config_mesas_container.controls.append(fila)
            
            page.update()
            
        except ValueError:
            pass

    def guardar_configuracion_mesas(e):
        config_data = []
        try:
            for item in mesas_inputs:
                numero = item["numero"]
                capacidad_str = item["input"].value
                if not capacidad_str:
                    capacidad = 4 # Default fallback
                else:
                    capacidad = int(capacidad_str)
                
                config_data.append({"numero": numero, "capacidad": capacidad})
            
            # Llamar al backend
            backend_service.configurar_mesas(config_data)
            
            page.snack_bar = ft.SnackBar(ft.Text("Configuración de mesas guardada exitosamente."), bgcolor=ft.Colors.GREEN_700)
            page.snack_bar.open = True
            
            # Notificar para actualizar UI principal si es necesario
            if on_update_ui:
                on_update_ui()
                
            page.update()
            
        except Exception as ex:
            print(f"Error guardando mesas: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Error al guardar: {ex}"), bgcolor=ft.Colors.RED_700)
            page.snack_bar.open = True
            page.update()

    def cargar_mesas_existentes():
        try:
            mesas = backend_service.obtener_mesas()
            # Filtrar mesa virtual y ordenar
            mesas_reales = sorted([m for m in mesas if not m.get("es_virtual", False) and m["numero"] != 99], key=lambda x: x["numero"])
            
            if mesas_reales:
                total_mesas_input.value = str(len(mesas_reales))
                config_mesas_container.controls.clear()
                mesas_inputs.clear()
                
                for m in mesas_reales:
                    num = m["numero"]
                    cap = m["capacidad"]
                    
                    input_capacidad = ft.TextField(
                        label=f"Capacidad Mesa {num}",
                        value=str(cap),
                        width=150,
                        input_filter=ft.NumbersOnlyInputFilter()
                    )
                    mesas_inputs.append({"numero": num, "input": input_capacidad})
                    
                    fila = ft.Row([
                        ft.Text(f"Mesa {num}:", weight=ft.FontWeight.BOLD, width=80),
                        input_capacidad,
                        ft.Text("personas")
                    ])
                    config_mesas_container.controls.append(fila)
                page.update()
            else:
                generar_inputs_mesas(None)

        except Exception as e:
            print(f"Error cargando mesas existentes: {e}")

    btn_generar = ft.ElevatedButton("Generar Campos", on_click=generar_inputs_mesas)
    btn_guardar_mesas = ft.ElevatedButton("Guardar Configuración Mesas", on_click=guardar_configuracion_mesas, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)

    tab_mesas = ft.Container(
        content=ft.Column([
            ft.Text("Configuración de Mesas", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("Define cuántas mesas tiene tu restaurante y su capacidad.", size=14, color=ft.Colors.GREY_400),
            ft.Row([
                total_mesas_input,
                btn_generar
            ]),
            ft.Divider(),
            ft.Text("Detalle por Mesa:", size=16),
            config_mesas_container,
            ft.Divider(),
            btn_guardar_mesas
        ]),
        padding=20
    )

    # --- INICIALIZACIÓN ---
    cargar_datos_menu()
    cargar_mesas_existentes()

    t = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Menú y Platillos", content=tab_menu),
            ft.Tab(text="Configurar Mesas", content=tab_mesas),
        ],
        expand=True,
    )

    return t
