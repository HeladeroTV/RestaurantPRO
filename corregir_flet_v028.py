import os
import re

def corregir_flet_v028(directorio):
    """
    Busca y reemplaza ft.colors por ft.Colors y ft.icons por ft.Icons en archivos .py
    para compatibilidad con Flet v0.28
    """
    for root, dirs, files in os.walk(directorio):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    contenido = f.read()

                # Reemplazar ft.colors por ft.Colors
                contenido_corregido = re.sub(r'\bft\.colors\.', 'ft.Colors.', contenido)
                # Reemplazar ft.icons por ft.Icons
                contenido_corregido = re.sub(r'\bft\.icons\.', 'ft.Icons.', contenido_corregido)

                if contenido != contenido_corregido:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(contenido_corregido)
                    print(f"✅ Corregido: {filepath}")

if __name__ == "__main__":
    directorio = input("Introduce la ruta de la carpeta donde están tus archivos .py: ").strip()
    if not os.path.isdir(directorio):
        print("❌ Ruta inválida.")
    else:
        corregir_flet_v028(directorio)
        print("✅ Corrección completada.")