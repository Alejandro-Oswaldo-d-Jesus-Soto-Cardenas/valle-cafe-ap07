# Guía práctica de despliegue Valle Café AP07

## 1. AWS: seguridad de red

Región sugerida `us-east-1`. Crear un RDS MySQL privado en la **misma VPC** de la EC2.

- RDS → Conectividad y seguridad → **Acceso público: No**.
- `sg-web` / EC2, entrada: SSH TCP **22 desde `TU_IP_PUBLICA/32`** (y la IP de cada compañero, individualmente). TCP **5000 desde las IP autorizadas** para mostrar la web (o rango permitido por el profesor).
- `sg-rds` / RDS, entrada: MySQL TCP **3306 con origen `sg-web`** (ID del Security Group, no `0.0.0.0/0`). No crear regla 3306 pública.
- Las reglas de salida deben permitir la comunicación EC2 → RDS. Comprobar RDS en subredes alcanzables dentro de la VPC y tablas de rutas/NACL.
- Capturar pantallas con SG, acceso público, EC2 y RDS. **No exponer nombres de usuario con contraseñas, PEM o tokens.**

## 2. Preparar MySQL desde Ubuntu (EC2)

Subir el proyecto a EC2 mediante Git o SCP. Instalar el cliente:

```bash
sudo apt update
sudo apt install -y mysql-client python3-venv python3-pip
```

Descargar `global-bundle.pem` del trust store oficial RDS en EC2. La conexión administrativa puede hacerse así:

```bash
mysql -h ENDPOINT_RDS -P 3306 -u USUARIO_MAESTRO -p --ssl-mode=VERIFY_IDENTITY --ssl-ca=/home/ubuntu/global-bundle.pem
```

Ya en el cliente `mysql>`:

```sql
SOURCE /home/ubuntu/valle-cafe-ap07/database/schema.sql;
SOURCE /home/ubuntu/valle-cafe-ap07/database/usuarios.example.sql;
SOURCE /home/ubuntu/valle-cafe-ap07/database/datos_prueba.sql;
SHOW GRANTS FOR 'app_web'@'%';
SHOW GRANTS FOR 'app_desktop'@'%';
```

**Antes de ejecutar `usuarios.example.sql`, reemplazar las contraseñas de ejemplo por otras fuertes y únicas en una COPIA LOCAL del script, sin subirla a Git.** Para mayor seguridad, ejecutar los `CREATE USER` y `GRANT` manualmente, evitando guardar contraseñas en archivos. El script de datos se ejecuta **una sola vez**.

## 3. Servidor web Flask

```bash
cd /home/ubuntu/valle-cafe-ap07/web
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Editar el archivo privado `.env`: `DB_HOST` = endpoint RDS, `DB_NAME=valle_cafe`, `DB_USER=app_web`, `DB_PASSWORD` = secreto único, `DB_SSL_CA=/home/ubuntu/global-bundle.pem`, `SECRET_KEY` aleatoria fuerte, `ADMIN_USER` y `ADMIN_PASSWORD` distintos de MySQL para el panel `/admin`. Protegerlo:

```bash
chmod 600 .env
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

Abrir desde una IP permitida: `http://IP_PUBLICA_EC2:5000/`. La portada es una tienda para el público con menú, carrito y seguimiento; el CRUD administrativo está en `/admin`, protegido con credenciales distintas de las de MySQL. Confirmar `http://IP_PUBLICA_EC2:5000/health` (debe decir `connected`). **No exponer `/admin` a Internet por HTTP sin HTTPS**: la autenticación HTTP Basic solo se incluye como protección de laboratorio; para producción agregar HTTPS, sesiones, CSRF y límites de solicitudes. Para mantener Flask funcionando tras cerrar SSH, copiar y adaptar `deploy/valle-cafe.service.example` como servicio systemd:

```bash
sudo cp /home/ubuntu/valle-cafe-ap07/deploy/valle-cafe.service.example /etc/systemd/system/valle-cafe.service
sudo systemctl daemon-reload
sudo systemctl enable --now valle-cafe
sudo systemctl status valle-cafe
```

Si ejecutas con Gunicorn manualmente no necesitas iniciar simultáneamente el servicio (puerto 5000 ocupado).

## 4. Java Swing + túnel SSH automático

En Windows instalar **JDK 17+ y Maven**. En `desktop/`:

```powershell
Copy-Item config.properties.example config.properties
notepad config.properties
mvn clean compile exec:java
```

Completar IP pública vigente EC2, `ssh.user=ubuntu`, `.pem`, ruta de `known_hosts`, endpoint privado de RDS y `db.user=app_desktop`. La primera conexión SSH debe haber verificado y guardado la huella del servidor en `known_hosts` (por ejemplo, mediante `ssh -i C:\ruta\KeyUb.pem ubuntu@IP_EC2`, verificando la huella por un canal confiable). No poner una contraseña real en el `.example`.

Java abre automáticamente el túnel local `127.0.0.1:3308` → EC2:22 → RDS:3306 al iniciar, establece JDBC (TLS requerido) y cierra conexión/túnel al salir. Solo una app puede ocupar el puerto local 3308: si está ocupado, cerrar el otro túnel o elegir otro puerto libre. Workbench puede usar túnel integrado independiente.

## 5. MySQL Workbench por SSH

Crear conexión → **Standard TCP/IP over SSH**:

| Campo | Valor |
|---|---|
| SSH Hostname | `IP_PUBLICA_EC2:22` |
| SSH Username | `ubuntu` |
| SSH Key File | Ruta local a `.pem` |
| MySQL Hostname | Endpoint privado de RDS |
| MySQL Server Port | `3306` |
| Username | `app_desktop` para consultar datos; maestro solo para administrar |
| Default Schema | `valle_cafe` |

Consulta para verificar:

```sql
SELECT p.id, c.nombre, p.producto, p.cantidad, p.precio_unitario, p.estado
FROM valle_cafe.pedidos p JOIN valle_cafe.clientes c ON c.id = p.cliente_id
ORDER BY p.id DESC;
```

## 6. Evidencias obligatorias y pruebas

1. **INSERT web → escritorio:** Registrar un cliente, registrar un pedido (p. ej., Latte Vainilla). Pulsar **Actualizar lista** en Java; comprobar el mismo ID y valores en Workbench.
2. **UPDATE escritorio → web:** Seleccionar el pedido Java, cambiar estado a `Listo` y pulsar **Editar seleccionado**. Recargar web y Workbench.
3. **INSERT escritorio → web:** Crear otro pedido Java. Recargar web para comprobarlo.
4. **UPDATE web → escritorio:** Editar precio o cantidad en web; pulsar **Actualizar lista** en Java.
5. **DELETE web o escritorio:** Borrar un pedido de prueba; confirmar que ya no existe en ambas interfaces y Workbench.
6. **Prueba red:** desde Windows, intentar conexión TCP directa a `ENDPOINT_RDS:3306` sin túnel. Debe fallar porque RDS es privado; comprobar `Acceso público: No`.
7. **Prueba permisos (sin daño):** conectado como `app_desktop`, ejecutar `SHOW GRANTS FOR CURRENT_USER();` y `CREATE TABLE valle_cafe.prueba_permiso(id INT);` (debe fallar por permiso insuficiente). **No probar DROP TABLE con una tabla real.**
8. Documentar dos fallos simulados (SSH22 desde IP no autorizada; credenciales erróneas) y sus soluciones sin publicar contraseñas.

## 7. Checklist final

- [ ] RDS privado, SG sólo desde sg-web en 3306.
- [ ] SSH22 restringido al /32 de cada integrante; revisar IP nueva si EC2 se reinicia.
- [ ] Usuarios `app_web` / `app_desktop` con solo 4 privilegios CRUD.
- [ ] Dos tablas relacionadas `clientes` / `pedidos`.
- [ ] Web y escritorio ejecutan CRUD y comparten los registros.
- [ ] Backup SQL sin secretos y/o snapshot RDS, previo a cambios mayores.
- [ ] `.gitignore` impide versionar contraseñas, `.pem`, `.env` y `config.properties`.
- [ ] Informe con capturas, repositorio y video 5–8 min, cámara y explicación según profesor.
- [ ] Cada integrante entrega individualmente y comenta nombres completos.
- [ ] Quitar reglas temporales SSH22 al finalizar, revisar costos de EC2/RDS y snapshots.
