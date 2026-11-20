# AP07 — Plantilla para informe y video

## Informe técnico (copiar en Google Docs y completar con capturas REALES)

**Título:** Valle Café: sistema híbrido multiplataforma en AWS con Flask, Java Swing y MySQL RDS privado.

**Curso:** S16 | AP07 — Proyecto práctico.

**Equipo:** [Nombres completos]. **Fecha:** [Fecha]. **Repositorio:** [URL GitHub/GitLab].

### 1. Resumen

Se desarrolló Valle Café, una solución de pedidos para una cafetería que integra una tienda web pública en Python Flask desplegada en EC2, un panel administrativo privado y una aplicación Java Swing ejecutada localmente. La tienda permite explorar el menú, agregar productos a un carrito y registrar pedidos sin pago. Todas las operaciones utilizan una base MySQL de Amazon RDS privada. La aplicación de escritorio accede mediante un túnel SSH programático a EC2 con JSch y utiliza JDBC para consultar o modificar registros. El servidor Flask se conecta directamente a RDS desde la VPC.

### 2. Objetivos

- Construir dos aplicaciones nuevas e independientes que compartan una única base relacional.
- Proteger RDS sin acceso público, restringiendo los puertos mediante Security Groups.
- Configurar usuarios independientes con privilegios CRUD limitados.
- Demostrar sincronización funcional y errores esperados de seguridad.

### 3. Arquitectura

**Figura 1.** [Pegar diagrama de `README.md` o su versión dibujada].

**Descripción:** Navegador → EC2 Flask:5000 → RDS:3306 por VPC. Java local → EC2:22 (SSH JSch) → RDS:3306, con JDBC local a `127.0.0.1:3308`. Workbench → túnel SSH EC2 → RDS. RDS público: **No**.

**Figura 2.** [AWS EC2 — IP pública y estado En ejecución].

**Figura 3.** [AWS RDS — Acceso público = No].

**Figura 4.** [SG EC2: 22 desde /32 de integrantes y 5000 según requisitos].

**Figura 5.** [SG RDS: 3306 desde identificador SG EC2, no desde Internet].

### 4. Modelo de datos y credenciales

**Figura 6.** [MySQL Workbench: schema `valle_cafe`, tablas `clientes` y `pedidos`, relación FK].

**Figura 7.** [Resultado SQL `SHOW GRANTS FOR 'app_web'@'%'` y `SHOW GRANTS FOR 'app_desktop'@'%'`].

Las tablas están relacionadas mediante `pedidos.cliente_id → clientes.id`. Cada cliente tiene nombre, teléfono y correo; cada pedido posee producto, cantidad, precio y estado. Los usuarios de las aplicaciones poseen únicamente `SELECT`, `INSERT`, `UPDATE` y `DELETE` en `valle_cafe.*`.

### 5. Implementación de aplicaciones

**Figura 8.** [Terminal Ubuntu con `gunicorn` activo, o `systemctl status valle-cafe`].

**Figura 9.** [Tienda Valle Café en EC2:5000, carrito y panel privado `/admin`].

**Figura 10.** [Desktop Java conectado: etiqueta SSH + JDBC].

**Figura 11.** [Workbench conectado por Standard TCP/IP over SSH].

### 6. Resultados de integración

| Caso | Acción | Resultado real | Evidencia |
|---|---|---|---|
| P01 | INSERT desde web y lectura en Java/Workbench | [Completar] | [Captura] |
| P02 | UPDATE desde Java y lectura en web/Workbench | [Completar] | [Captura] |
| P03 | INSERT desde Java y lectura en web | [Completar] | [Captura] |
| P04 | UPDATE desde web y lectura en Java | [Completar] | [Captura] |
| P05 | DELETE de pedido y consulta en ambas apps | [Completar] | [Captura] |

### 7. Validación de seguridad

**Figura 12.** [Conexión directa desde Windows a RDS:3306 bloqueada].

**Figura 13.** [Usuario app_desktop: `CREATE TABLE` denegado; capturar solo el error].

**Figura 14.** [`.gitignore` y archivos `.example` sin contraseñas].

La base de datos no admite acceso directo desde Internet. La EC2 funciona como servidor puente para clientes SSH autorizados. Los usuarios de las aplicaciones no tienen permisos de administración ni alteración del esquema.

### 8. Conclusiones

Valle Café demuestra una arquitectura híbrida que combina Flask en EC2, Java Swing en una PC y una base RDS privada. Las aplicaciones intercambian información mediante consultas a un mismo esquema, mientras que el túnel SSH habilita el acceso remoto sin publicar la base de datos. Las restricciones de red y de usuarios reducen los privilegios disponibles para el funcionamiento normal del sistema. **Ajustar la redacción final según los resultados realmente observados.**

### 9. Enlaces de entrega

- Repositorio: [URL]
- Google Docs (lectura/comentario): [URL]
- Video 5–8 min: [URL]
- Integrantes: [Nombres completos]

---

## Guion para video de 5–8 minutos (distribuir entre integrantes)

| Tiempo | Pantalla y acción | Guion sugerido |
|---|---|---|
| 0:00–0:40 | Presentación y diagrama | «Somos el equipo […]. Presentamos Valle Café, un sistema nuevo de pedidos que une una aplicación web Flask en AWS, un escritorio Java y un MySQL RDS privado. Ambas aplicaciones trabajan con los mismos registros». |
| 0:40–1:35 | AWS EC2/RDS y SG | «RDS indica Acceso público: No. El Security Group de RDS permite 3306 solo desde el SG de EC2. Para SSH 22 solo autorizamos nuestras IP /32. La web funciona por el puerto 5000». |
| 1:35–2:15 | Workbench esquema y GRANT | «Hay dos tablas: clientes y pedidos, unidas por una clave foránea. Creamos `app_web` y `app_desktop` con permisos SELECT, INSERT, UPDATE y DELETE, sin permisos para alterar tablas». |
| 2:15–3:05 | Tienda web — elegir producto y checkout | «La página pública ofrece un menú y carrito. Agrego Latte Vainilla, completo los datos de un cliente y confirmo. Flask registra el pedido en la misma base de datos RDS». |
| 3:05–4:00 | Java — conectar/actualizar y editar | «En Java se establece automáticamente un túnel SSH con JSch a EC2; JDBC utiliza el puerto local 3308. Aquí aparece el mismo pedido. Cambio su estado a Listo y lo guardo». |
| 4:00–4:50 | Refrescar web y Workbench | «Recargo la web y comprobamos que el estado cambió. En Workbench ejecuto una consulta a ambas tablas y encuentro el mismo ID y el estado actualizado». |
| 4:50–5:40 | Crear en Java, editar en web y borrar | «Ahora registro otro pedido desde el escritorio, lo verifico en la web, cambio la cantidad desde Flask y actualizo Java. Finalmente elimino un pedido de prueba y verifico que desaparece». |
| 5:40–6:40 | Prueba red y SQL de permiso | «Una conexión directa desde mi equipo a RDS:3306 falla porque es privado. También comprobamos que `app_desktop` no puede crear tablas. Los accesos están limitados a lo necesario». |
| 6:40–7:15 | Repositorio y cierre | «El repositorio contiene las dos aplicaciones, `schema.sql`, configuraciones de ejemplo y `.gitignore`, sin contraseñas ni archivos PEM. Concluimos que web y escritorio comparten datos con acceso remoto seguro por SSH». |

**Antes de grabar:** Abrir AWS, web, Java, terminal y Workbench; confirmar que las apps se conectan, tener clientes creados y mostrar todas las acciones **en tiempo real**. Adaptar el texto a lo que de verdad funcione. Cámara activa y participación de todos si el docente lo exige. **Nunca mostrar archivos reales con credenciales ni escribir contraseñas mientras graban.**
