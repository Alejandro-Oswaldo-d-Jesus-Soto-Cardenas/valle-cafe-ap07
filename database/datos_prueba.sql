USE valle_cafe;
INSERT INTO clientes (nombre, telefono, correo) VALUES
 ('Ana Torres', '999111222', 'ana.torres@example.com'),
 ('Luis Ramos', '999333444', 'luis.ramos@example.com'),
 ('María López', '999555666', 'maria.lopez@example.com');
INSERT INTO pedidos (cliente_id, producto, cantidad, precio_unitario, estado)
SELECT id, 'Latte Vainilla', 2, 13.50, 'Pendiente' FROM clientes WHERE correo='ana.torres@example.com';
INSERT INTO pedidos (cliente_id, producto, cantidad, precio_unitario, estado)
SELECT id, 'Cold Brew', 1, 12.00, 'Preparando' FROM clientes WHERE correo='luis.ramos@example.com';

