-- Ejecutar SOLO con el usuario administrador de RDS, después de schema.sql.
-- Reemplazar las contraseñas de ejemplo de forma privada; no guardar secretos reales en Git.
CREATE USER IF NOT EXISTS 'app_web'@'%' IDENTIFIED BY 'REEMPLAZAR_CON_SECRETO_UNICO_WEB';
CREATE USER IF NOT EXISTS 'app_desktop'@'%' IDENTIFIED BY 'REEMPLAZAR_CON_SECRETO_UNICO_DESKTOP';
GRANT SELECT, INSERT, UPDATE, DELETE ON valle_cafe.* TO 'app_web'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON valle_cafe.* TO 'app_desktop'@'%';
-- Comprobar: SHOW GRANTS FOR 'app_desktop'@'%';
-- No otorgar CREATE, ALTER, DROP, GRANT OPTION, ni privilegios globales.

