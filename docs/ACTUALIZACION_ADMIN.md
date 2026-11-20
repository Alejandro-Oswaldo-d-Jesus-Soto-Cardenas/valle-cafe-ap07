# Valle Café — actualización del panel administrativo

Esta actualización modifica **solo la interfaz administrativa** y pasa al template la lista de productos existente.
No cambia tablas, usuarios, permisos ni registros de AWS RDS. Los pedidos actuales se conservan.

## Aplicar en Windows y EC2

1. Descarga el ZIP de actualización, extráelo y copia sus archivos a las mismas rutas dentro de tu carpeta `valle-cafe-ap07` local.
2. Desde PowerShell, situado en la carpeta raíz del proyecto, sube los archivos a tu EC2. Sustituye `IP_PUBLICA_EC2` por la IP actual:

   ```powershell
   scp -i "C:\Users\Administrator\Documents\KeyUb.pem" web/app.py ubuntu@IP_PUBLICA_EC2:/home/ubuntu/valle-cafe-ap07/web/app.py
   scp -i "C:\Users\Administrator\Documents\KeyUb.pem" web/templates/admin.html ubuntu@IP_PUBLICA_EC2:/home/ubuntu/valle-cafe-ap07/web/templates/admin.html
   scp -i "C:\Users\Administrator\Documents\KeyUb.pem" web/static/admin.css ubuntu@IP_PUBLICA_EC2:/home/ubuntu/valle-cafe-ap07/web/static/admin.css
   scp -i "C:\Users\Administrator\Documents\KeyUb.pem" web/static/admin.js ubuntu@IP_PUBLICA_EC2:/home/ubuntu/valle-cafe-ap07/web/static/admin.js
   ```

3. Conéctate por SSH a EC2 y ejecuta:

   ```bash
   sudo systemctl restart valle-cafe
   sudo systemctl status valle-cafe --no-pager
   ```

4. Entra a `/admin` y actualiza con **Ctrl+F5** para recargar los estilos.

## Comprobaciones

- Resumen: pedidos, clientes e importe total siguen coincidiendo con RDS y Java.
- Pedidos: crear, editar y eliminar continúan funcionando.
- Clientes: alta y búsqueda visual.
- Catálogo: consulta de menú, sin edición de precios por ahora.
- Reportes: datos acumulados sobre los registros existentes, sin asumir pagos cobrados.

## Seguridad pendiente

El login HTTP Basic en `http://IP:5000/admin` **no es seguro para producción**: evita usar credenciales administrativas reales por HTTP. Configura HTTPS y una autenticación con sesión/CSRF antes de exponerlo al público. No publiques `.env`, `desktop/config.properties` ni las llaves `.pem` en Git.
