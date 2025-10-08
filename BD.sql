-- =============================================================
-- SCHEMA DE RESTAURANTIA (PostgreSQL)
-- Ejecutar dentro de la base de datos "restaurant_db"
-- Si aún no existe la base:
--   CREATE DATABASE restaurant_db;
--   \c restaurant_db
-- =============================================================

-- ==========================
-- Tabla: menu
-- ==========================
CREATE TABLE IF NOT EXISTS menu (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    precio NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    tipo VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_menu_tipo ON menu(tipo);
CREATE UNIQUE INDEX IF NOT EXISTS idx_menu_nombre_tipo ON menu(nombre, tipo);

-- ==========================
-- Tabla: pedidos
-- ==========================
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    mesa_numero INTEGER NOT NULL CHECK (mesa_numero > 0),
    numero_app INTEGER,
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    fecha_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    items JSONB NOT NULL,
    notas TEXT DEFAULT '',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);
CREATE INDEX IF NOT EXISTS idx_pedidos_mesa ON pedidos(mesa_numero);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado_fecha ON pedidos(estado, fecha_hora DESC);

-- Trigger para mantener updated_at actualizado
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'touch_pedidos_updated_at'
    ) THEN
        CREATE OR REPLACE FUNCTION touch_pedidos_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_pedidos_updated_at'
    ) THEN
        CREATE TRIGGER trg_pedidos_updated_at
        BEFORE UPDATE ON pedidos
        FOR EACH ROW
        EXECUTE FUNCTION touch_pedidos_updated_at();
    END IF;
END$$;

-- ==========================
-- Tabla: clientes
-- ==========================
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    domicilio VARCHAR(255) NOT NULL,
    celular VARCHAR(50) NOT NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre);

-- ==========================
-- Tabla: inventario
-- ==========================
CREATE TABLE IF NOT EXISTS inventario (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    cantidad_disponible INTEGER NOT NULL CHECK (cantidad_disponible >= 0),
    unidad_medida VARCHAR(50) NOT NULL DEFAULT 'unidad',
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_inventario_nombre ON inventario(nombre);

-- Trigger para mantener fecha_actualizacion
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'touch_inventario_actualizacion'
    ) THEN
        CREATE OR REPLACE FUNCTION touch_inventario_actualizacion()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
            RETURN NEW;
        END; $$ LANGUAGE plpgsql;
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_inventario_actualizacion'
    ) THEN
        CREATE TRIGGER trg_inventario_actualizacion
        BEFORE UPDATE ON inventario
        FOR EACH ROW
        EXECUTE FUNCTION touch_inventario_actualizacion();
    END IF;
END$$;

-- =============================================================
-- FIN DEL SCHEMA
-- =============================================================
