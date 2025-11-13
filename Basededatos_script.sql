-- === COMANDOS SQL PARA CREAR LA BASE DE DATOS COMPLETA ===

-- 1. CREAR LA BASE DE DATOS (opcional si ya existe)
-- Este comando se ejecuta en la base de datos 'postgres' o en una base de superusuario
CREATE DATABASE restaurant_db;

-- 2. CONECTARSE A LA BASE DE DATOS (esto se hace en la herramienta de cliente, no en SQL puro)
-- \c restaurant_db; -- En psql

-- 3. CREAR LAS TABLAS EN LA BASE DE DATOS restaurant_db

-- 3.1. TABLA: mesas
-- Almacena la información de las mesas físicas y la mesa virtual.
CREATE TABLE IF NOT EXISTS mesas (
    id SERIAL PRIMARY KEY,
    numero INTEGER NOT NULL UNIQUE, -- Ej: 1, 2, ..., 6, 99
    capacidad INTEGER NOT NULL DEFAULT 1, -- Número de comensales
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar mesas iniciales (físicas y virtual) si no existen
INSERT INTO mesas (numero, capacidad) VALUES
(1, 2), (2, 2), (3, 4), (4, 4), (5, 6), (6, 6), (99, 100) -- Mesa virtual
ON CONFLICT (numero) DO NOTHING;

-- 3.2. TABLA: menu
-- Almacena los items disponibles en el menú.
CREATE TABLE IF NOT EXISTS menu (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    precio REAL NOT NULL,
    tipo TEXT NOT NULL -- Ej: 'Entradas', 'Platos Fuertes', 'Postres', 'Bebidas'
);

-- 3.3. TABLA: clientes
-- Almacena la información de los clientes registrados.
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    domicilio TEXT,
    celular TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.4. TABLA: pedidos
-- Almacena cada pedido realizado.
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    mesa_numero INTEGER NOT NULL,
    cliente_id INTEGER, -- Puede ser NULL si no es cliente registrado o es pedido digital
    estado TEXT NOT NULL DEFAULT 'Tomando pedido', -- 'Tomando pedido', 'Pendiente', 'En preparacion', 'Listo', 'Entregado', 'Pagado'
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    items JSONB NOT NULL DEFAULT '[]'::jsonb, -- Almacena el array de ítems como JSON
    numero_app INTEGER, -- Para identificar pedidos de la app digital (asignado cuando mesa_numero = 99)
    notas TEXT DEFAULT '', -- Notas del pedido
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Útil para rastrear modificaciones
    FOREIGN KEY (mesa_numero) REFERENCES mesas(numero) ON DELETE SET NULL, -- Si se borra la mesa, el pedido queda sin mesa
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL -- Si se borra el cliente, el pedido queda sin cliente
);

-- Índices para optimizar consultas comunes
CREATE INDEX IF NOT EXISTS idx_pedidos_estado_fecha ON pedidos (estado, fecha_hora DESC);
CREATE INDEX IF NOT EXISTS idx_pedidos_mesa_estado_activos ON pedidos (mesa_numero, estado) WHERE estado IN ('Pendiente', 'En preparacion', 'Listo');

-- 3.5. TABLA: inventario
-- Almacena los items del inventario.
CREATE TABLE IF NOT EXISTS inventario (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE, -- Nombre del ingrediente o producto
    descripcion TEXT,
    cantidad_disponible REAL NOT NULL DEFAULT 0,
    unidad_medida TEXT NOT NULL, -- Ej: 'kg', 'g', 'lt', 'ml', 'unidades', 'docenas'
    cantidad_minima REAL DEFAULT 0, -- Nivel mínimo antes de alertar
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.6. TABLA: recetas
-- Almacena las recetas de los platos.
CREATE TABLE IF NOT EXISTS recetas (
    id SERIAL PRIMARY KEY,
    nombre_plato TEXT NOT NULL UNIQUE, -- Nombre del plato del menú (debe coincidir con menu.nombre)
    descripcion TEXT,                 -- Descripción opcional de la receta
    instrucciones TEXT,               -- Pasos para preparar la receta
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nombre_plato) REFERENCES menu(nombre) ON DELETE CASCADE -- Si se borra el plato, se borra la receta
);

-- 3.7. TABLA: ingredientes_recetas
-- Relaciona los ingredientes (del inventario) con las recetas y la cantidad necesaria.
CREATE TABLE IF NOT EXISTS ingredientes_recetas (
    id SERIAL PRIMARY KEY,
    receta_id INTEGER NOT NULL,
    ingrediente_id INTEGER NOT NULL,
    cantidad_necesaria REAL NOT NULL, -- Cantidad del ingrediente necesaria para una unidad del plato
    unidad_medida_necesaria TEXT NOT NULL, -- Unidad de medida necesaria (ej: 'g', 'kg', 'ml', 'unidad')
    FOREIGN KEY (receta_id) REFERENCES recetas(id) ON DELETE CASCADE, -- Si se borra la receta, se borra el ingrediente de la receta
    FOREIGN KEY (ingrediente_id) REFERENCES inventario(id) ON DELETE RESTRICT -- Si un ingrediente se usa en una receta, no se puede borrar del inventario
);

-- Opcional: Crear un índice para optimizar la búsqueda de ingredientes por receta
CREATE INDEX IF NOT EXISTS idx_ingredientes_recetas_receta_id ON ingredientes_recetas (receta_id);

-- 3.8. TABLA: configuraciones
-- Almacena configuraciones generales del sistema, específicamente para listas de ingredientes.
CREATE TABLE IF NOT EXISTS configuraciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,          -- Nombre de la configuración (ej: "Stock Inicial", "Promo Semanal")
    descripcion TEXT,                     -- Descripción de la configuración
    ingredientes JSONB NOT NULL DEFAULT '[]'::jsonb  -- Array de ingredientes como JSON: [{"nombre": "...", "cantidad": ..., "unidad": "..."}, ...]
);

-- 3.9. TABLA: reservas (si la implementaste)
-- Almacena las reservas de mesas.
CREATE TABLE IF NOT EXISTS reservas (
    id SERIAL PRIMARY KEY,
    mesa_numero INTEGER NOT NULL,
    cliente_id INTEGER NOT NULL,
    fecha_hora_inicio TIMESTAMP NOT NULL,
    fecha_hora_fin TIMESTAMP, -- Opcional
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mesa_numero) REFERENCES mesas(numero) ON DELETE CASCADE, -- Si se borra la mesa, se borra la reserva
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE  -- Si se borra el cliente, se borra la reserva
);

-- Índice para optimizar la consulta de mesas disponibles
CREATE INDEX IF NOT EXISTS idx_reservas_fecha_hora ON reservas (fecha_hora_inicio, fecha_hora_fin);

-- Opcional: Insertar una configuración de ejemplo
-- INSERT INTO configuraciones (nombre, descripcion, ingredientes) VALUES
-- ('Stock Basico', 'Ingredientes iniciales comunes', '[{"nombre": "Pollo", "cantidad": 10, "unidad": "kg"}, {"nombre": "Arroz", "cantidad": 5, "unidad": "kg"}]')
-- ON CONFLICT (nombre) DO NOTHING;

-- 4. OPCIONAL: Insertar algunos items de ejemplo en el menú
-- Puedes usar el endpoint /menu/inicializar de backend.py para esto también.
-- INSERT INTO menu (nombre, precio, tipo) VALUES
-- ('Empanada Kunai', 70.00, 'Entradas'),
-- ('Camarones roca', 160.00, 'Platillos'),
-- ('Yakimeshi Especial', 150.00, 'Arroces')
-- ON CONFLICT (nombre) DO NOTHING; -- Evita errores si ya existen

-- 5. OPCIONAL: Insertar clientes de ejemplo
-- INSERT INTO clientes (nombre, domicilio, celular) VALUES
-- ('Juan Pérez', 'Calle Falsa 123', '5551234567'),
-- ('Ana Gómez', 'Avenida Siempre Viva 742', '5559876543')
-- ON CONFLICT (id) DO NOTHING; -- Asumiendo ID autoincremental, ON CONFLICT no aplica directamente aquí, pero puedes usar DO NOTHING si insertas con ID fijo
-- Mejor usar DO NOTHING con un campo único como nombre si es PK compuesta o manejarlo en la app.
-- INSERT INTO clientes (nombre, domicilio, celular) VALUES
-- ('Cliente Ejemplo 1', 'Direccion Ejemplo 1', '1111111111'),
-- ('Cliente Ejemplo 2', 'Direccion Ejemplo 2', '2222222222');

-- 6. OPCIONAL: Insertar inventario de ejemplo
-- INSERT INTO inventario (nombre, descripcion, cantidad_disponible, unidad_medida, cantidad_minima) VALUES
-- ('Pollo', 'Pechuga de pollo fresco', 20.0, 'kg', 5.0),
-- ('Arroz', 'Arroz blanco grano largo', 10.0, 'kg', 2.0),
-- ('Salsa de Soja', 'Salsa de soja light', 5.0, 'lt', 1.0)
-- ON CONFLICT (nombre) DO NOTHING;

-- 7. OPCIONAL: Insertar recetas de ejemplo (debes conocer los IDs de los items del menú e ingredientes del inventario)
-- INSERT INTO recetas (nombre, descripcion, instrucciones) VALUES
-- ('Yakimeshi Especial', 'Yakimeshi con camarones y verduras', 'Saltear arroz con verduras, agregar camarones y salsa.')
-- ON CONFLICT (nombre) DO NOTHING;
-- INSERT INTO ingredientes_recetas (receta_id, ingrediente_id, cantidad_necesaria, unidad_medida_necesaria) VALUES
-- (1, 1, 0.2, 'kg'), -- Suponiendo ID 1 para Yakimeshi Especial y ID 1 para Pollo
-- (1, 2, 0.1, 'kg'); -- Suponiendo ID 2 para Arroz
-- NOTA: Los IDs de receta e ingrediente deben existir. Es mejor hacerlo vía la app o con subconsultas si se conocen los nombres exactos.
-- Ejemplo con subconsulta (asumiendo unicidad de nombre):
-- INSERT INTO ingredientes_recetas (receta_id, ingrediente_id, cantidad_necesaria, unidad_medida_necesaria)
-- SELECT r.id, i.id, 0.2, 'kg'
-- FROM recetas r, inventario i
-- WHERE r.nombre = 'Yakimeshi Especial' AND i.nombre = 'Pollo'
-- ON CONFLICT DO NOTHING; -- No funciona directamente con subconsultas en todos los casos, requiere lógica más compleja o triggers si es estricto.

COMMIT; -- Asegurar que todas las operaciones se apliquen

-- Mensaje de confirmación (no es un comando SQL ejecutable, solo informativo)
-- echo "Base de datos 'restaurant_db' y tablas creadas exitosamente.";