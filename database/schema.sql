CREATE DATABASE IF NOT EXISTS valle_cafe CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE valle_cafe;

CREATE TABLE IF NOT EXISTS clientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  telefono VARCHAR(25) NOT NULL,
  correo VARCHAR(120) NOT NULL UNIQUE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pedidos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  producto VARCHAR(100) NOT NULL,
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(10,2) NOT NULL,
  estado ENUM('Pendiente', 'Preparando', 'Listo', 'Entregado') NOT NULL DEFAULT 'Pendiente',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pedidos_clientes FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
  CONSTRAINT ck_pedidos_cantidad CHECK (cantidad > 0),
  CONSTRAINT ck_pedidos_precio CHECK (precio_unitario > 0)
) ENGINE=InnoDB;

