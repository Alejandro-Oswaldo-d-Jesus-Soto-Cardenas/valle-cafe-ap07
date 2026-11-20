"""Valle Café AP07: aplicación web Flask con MySQL RDS privado."""
import os
import secrets
from decimal import Decimal, InvalidOperation
from functools import wraps

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for, Response

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "solo-desarrollo-local-cambiar-en-ec2")
ESTADOS = ("Pendiente", "Preparando", "Listo", "Entregado")
PRODUCTOS = ("Espresso", "Americano", "Cappuccino", "Latte Vainilla", "Mocha", "Cold Brew", "Frappé Caramelo", "Té Chai", "Croissant", "Cheesecake")

# Catálogo fijo y precios del SERVIDOR: nunca se acepta el precio enviado por el navegador.
MENU = [
    dict(id="espresso", nombre="Espresso de la casa", categoria="Calientes", precio=8.00, icono="☕", tono="cocoa", etiqueta="ESENCIAL", descripcion="Intenso, aromático y con carácter en cada sorbo."),
    dict(id="latte", nombre="Latte Vainilla", categoria="Calientes", precio=14.50, icono="🥛", tono="cream", etiqueta="MÁS PEDIDO", descripcion="Espresso suave, leche cremosa y notas de vainilla."),
    dict(id="capuccino", nombre="Cappuccino clásico", categoria="Calientes", precio=13.00, icono="☕", tono="olive", etiqueta="CLÁSICO", descripcion="Equilibrio perfecto de espresso, leche y espuma."),
    dict(id="mocha", nombre="Mocha de chocolate", categoria="Calientes", precio=16.00, icono="🍫", tono="mocha", etiqueta="IRRESISTIBLE", descripcion="Café de especialidad con chocolate sedoso."),
    dict(id="coldbrew", nombre="Cold Brew", categoria="Fríos", precio=15.00, icono="🧊", tono="sage", etiqueta="REFRESCANTE", descripcion="Café infusionado en frío, suave y lleno de sabor."),
    dict(id="frappe", nombre="Frappé Caramelo", categoria="Fríos", precio=18.50, icono="🥤", tono="honey", etiqueta="FAVORITO", descripcion="Cremoso, helado y con un toque dulce de caramelo."),
    dict(id="chai", nombre="Iced Chai Latte", categoria="Fríos", precio=16.50, icono="🍵", tono="mist", etiqueta="NUEVO", descripcion="Especias aromáticas, leche y un final fresco."),
    dict(id="croissant", nombre="Croissant artesanal", categoria="Panadería", precio=9.50, icono="🥐", tono="honey", etiqueta="RECIÉN HECHO", descripcion="Hojaldre dorado, crujiente por fuera y tierno por dentro."),
    dict(id="cheesecake", nombre="Cheesecake de frutos rojos", categoria="Panadería", precio=14.00, icono="🍰", tono="berry", etiqueta="DULCE MOMENTO", descripcion="Textura cremosa y el contraste perfecto de frutos rojos."),
    dict(id="cookie", nombre="Cookie de chocolate", categoria="Panadería", precio=7.50, icono="🍪", tono="cocoa", etiqueta="PARA COMPARTIR", descripcion="Galleta suave con generosos trozos de chocolate."),
]
PRODUCTOS_MENU = {item["id"]: item for item in MENU}


def solo_admin(funcion):
    @wraps(funcion)
    def protegida(*args, **kwargs):
        usuario = os.getenv("ADMIN_USER", "")
        clave = os.getenv("ADMIN_PASSWORD", "")
        auth = request.authorization
        if not usuario or not clave or not auth or not secrets.compare_digest(auth.username or "", usuario) or not secrets.compare_digest(auth.password or "", clave):
            return Response("Panel restringido. Configura ADMIN_USER y ADMIN_PASSWORD.", 401, {"WWW-Authenticate": 'Basic realm="Valle Cafe Administracion"'})
        return funcion(*args, **kwargs)
    return protegida


def conectar():
    config = {
        "host": os.environ["DB_HOST"],
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME", "valle_cafe"),
        "user": os.getenv("DB_USER", "app_web"),
        "password": os.environ["DB_PASSWORD"],
        "connection_timeout": 6,
    }
    ca = os.getenv("DB_SSL_CA")
    if ca:
        config.update(ssl_ca=ca, ssl_verify_cert=True, ssl_verify_identity=True)
    return mysql.connector.connect(**config)


def leer_pedido(form):
    try:
        cliente_id = int(form.get("cliente_id", ""))
        cantidad = int(form.get("cantidad", ""))
        precio = Decimal(form.get("precio_unitario", ""))
    except (TypeError, ValueError, InvalidOperation):
        raise ValueError("Cliente, cantidad y precio deben ser válidos.")
    producto = form.get("producto", "").strip()
    estado = form.get("estado", "Pendiente")
    if cliente_id < 1 or cantidad < 1 or not precio.is_finite() or precio <= 0 or precio > Decimal("99999999.99") or len(producto) > 100 or not producto or estado not in ESTADOS:
        raise ValueError("Revisa los datos del pedido (cantidad y precio mayores que cero).")
    return (cliente_id, producto, cantidad, precio, estado)


def ejecutar(sql, datos):
    db = conectar()
    try:
        cur = db.cursor()
        try:
            cur.execute(sql, datos)
            db.commit()
            return cur.rowcount
        except Exception:
            db.rollback()
            raise
        finally:
            cur.close()
    finally:
        db.close()


@app.get("/")
def inicio():
    return render_template("index.html", menu=MENU)


@app.get("/admin")
@solo_admin
def admin():
    try:
        db = conectar()
        try:
            cur = db.cursor(dictionary=True)
            try:
                cur.execute("SELECT id, nombre, telefono, correo FROM clientes ORDER BY nombre")
                clientes = cur.fetchall()
                cur.execute("""SELECT p.id, p.cliente_id, c.nombre AS cliente, p.producto,
                    p.cantidad, p.precio_unitario, p.estado, p.creado_en,
                    p.cantidad * p.precio_unitario AS total
                    FROM pedidos p JOIN clientes c ON c.id=p.cliente_id ORDER BY p.id DESC""")
                pedidos = cur.fetchall()
            finally:
                cur.close()
        finally:
            db.close()
        return render_template("admin.html", clientes=clientes, pedidos=pedidos, estados=ESTADOS, productos=MENU, error=False)
    except (mysql.connector.Error, KeyError, ValueError):
        return render_template("admin.html", clientes=[], pedidos=[], estados=ESTADOS, productos=MENU, error=True), 503


@app.post("/api/pedidos")
def pedido_publico():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Solicitud inválida."), 400
    nombre = str(data.get("nombre", "")).strip()
    correo = str(data.get("correo", "")).strip().lower()
    telefono = str(data.get("telefono", "")).strip()
    items = data.get("items")
    if not nombre or len(nombre) > 100 or not correo or "@" not in correo or len(correo) > 120 or not telefono or len(telefono) > 25:
        return jsonify(error="Completa correctamente tus datos."), 400
    if not isinstance(items, list) or not 1 <= len(items) <= len(MENU):
        return jsonify(error="El carrito está vacío o contiene demasiados productos."), 400
    normalizados = []
    vistos = set()
    for item in items:
        if not isinstance(item, dict):
            return jsonify(error="Producto inválido."), 400
        clave = item.get("id")
        cantidad = item.get("cantidad")
        if clave not in PRODUCTOS_MENU or clave in vistos or type(cantidad) is not int or cantidad < 1 or cantidad > 99:
            return jsonify(error="Revisa los productos o cantidades."), 400
        vistos.add(clave)
        normalizados.append((PRODUCTOS_MENU[clave], cantidad))
    db = None
    try:
        db = conectar()
        cur = db.cursor()
        try:
            cur.execute("SELECT id FROM clientes WHERE correo=%s", (correo,))
            actual = cur.fetchone()
            if actual:
                cliente_id = actual[0]
                # Evitar que alguien reutilice la identidad de otro cliente por correo.
                cur.execute("SELECT telefono FROM clientes WHERE id=%s", (cliente_id,))
                if cur.fetchone()[0] != telefono:
                    db.rollback()
                    return jsonify(error="Ese correo ya está registrado con otro teléfono."), 409
            else:
                cur.execute("INSERT INTO clientes(nombre,telefono,correo) VALUES (%s,%s,%s)", (nombre, telefono, correo))
                cliente_id = cur.lastrowid
            ids = []
            for producto, unidades in normalizados:
                cur.execute("INSERT INTO pedidos(cliente_id,producto,cantidad,precio_unitario,estado) VALUES (%s,%s,%s,%s,'Pendiente')", (cliente_id, producto["nombre"], unidades, producto["precio"]))
                ids.append(cur.lastrowid)
            db.commit()
            return jsonify(message="Pedido confirmado.", pedido_ids=ids), 201
        finally:
            cur.close()
    except (mysql.connector.Error, KeyError, ValueError):
        if db:
            db.rollback()
        return jsonify(error="No se pudo registrar el pedido. Comprueba que el servicio esté disponible."), 503
    finally:
        if db:
            db.close()


@app.get("/api/seguimiento")
def seguimiento():
    correo = request.args.get("correo", "").strip().lower()
    telefono = request.args.get("telefono", "").strip()
    if not correo or len(correo) > 120 or not telefono or len(telefono) > 25:
        return jsonify(error="Ingresa correo y teléfono para consultar."), 400
    try:
        db = conectar()
        try:
            cur = db.cursor(dictionary=True)
            try:
                cur.execute("""SELECT p.id,p.producto,p.cantidad,p.estado FROM pedidos p
                    JOIN clientes c ON p.cliente_id=c.id WHERE c.correo=%s AND c.telefono=%s ORDER BY p.id DESC LIMIT 30""", (correo, telefono))
                return jsonify(pedidos=cur.fetchall())
            finally:
                cur.close()
        finally:
            db.close()
    except (mysql.connector.Error, KeyError, ValueError):
        return jsonify(error="No se pudo consultar el estado ahora mismo."), 503


@app.post("/clientes")
@solo_admin
def crear_cliente():
    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    correo = request.form.get("correo", "").strip()
    if not nombre or not telefono or not correo or "@" not in correo or len(nombre) > 100 or len(telefono) > 25 or len(correo) > 120:
        flash("Completa correctamente los datos del cliente.", "error")
    else:
        try:
            ejecutar("INSERT INTO clientes(nombre,telefono,correo) VALUES (%s,%s,%s)", (nombre, telefono, correo))
            flash("Cliente registrado correctamente.", "ok")
        except (mysql.connector.Error, KeyError):
            flash("No se pudo registrar el cliente. Comprueba el correo o la conexión.", "error")
    return redirect(url_for("admin"))


@app.post("/pedidos")
@solo_admin
def crear_pedido():
    try:
        datos = leer_pedido(request.form)
        ejecutar("INSERT INTO pedidos(cliente_id,producto,cantidad,precio_unitario,estado) VALUES (%s,%s,%s,%s,%s)", datos)
        flash("Pedido registrado. Visible también en Java.", "ok")
    except (ValueError, mysql.connector.Error, KeyError) as exc:
        flash(str(exc) if isinstance(exc, ValueError) else "No se pudo registrar el pedido.", "error")
    return redirect(url_for("admin"))


@app.post("/pedidos/<int:pedido_id>/editar")
@solo_admin
def editar_pedido(pedido_id):
    try:
        datos = leer_pedido(request.form)
        filas = ejecutar("UPDATE pedidos SET cliente_id=%s, producto=%s, cantidad=%s, precio_unitario=%s, estado=%s WHERE id=%s", (*datos, pedido_id))
        flash("Pedido actualizado." if filas else "Pedido no encontrado.", "ok" if filas else "error")
    except (ValueError, mysql.connector.Error, KeyError) as exc:
        flash(str(exc) if isinstance(exc, ValueError) else "No se pudo actualizar el pedido.", "error")
    return redirect(url_for("admin"))


@app.post("/pedidos/<int:pedido_id>/eliminar")
@solo_admin
def eliminar_pedido(pedido_id):
    try:
        filas = ejecutar("DELETE FROM pedidos WHERE id=%s", (pedido_id,))
        flash("Pedido eliminado." if filas else "Pedido no encontrado.", "ok" if filas else "error")
    except (mysql.connector.Error, KeyError):
        flash("No se pudo eliminar el pedido.", "error")
    return redirect(url_for("admin"))


@app.get("/health")
def health():
    try:
        db = conectar()
        try:
            cur = db.cursor()
            try:
                cur.execute("SELECT 1")
                cur.fetchone()
            finally:
                cur.close()
        finally:
            db.close()
        return {"status": "ok", "database": "connected"}
    except (mysql.connector.Error, KeyError, ValueError):
        return {"status": "error", "database": "unavailable"}, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

