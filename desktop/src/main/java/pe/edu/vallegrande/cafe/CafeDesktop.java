package pe.edu.vallegrande.cafe;

import com.jcraft.jsch.JSch;
import com.jcraft.jsch.Session;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.InputStream;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Properties;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;

/** Cliente Java Swing independiente, con túnel SSH y JDBC a un RDS privado. */
public final class CafeDesktop extends JFrame {
    private static final Color VERDE = new Color(23, 68, 52);
    private static final Color CREMA = new Color(247, 245, 237);
    private static final String[] ESTADOS = {"Pendiente", "Preparando", "Listo", "Entregado"};
    private final Properties config = new Properties();
    private Session sesion;
    private Connection conexion;
    private final DefaultTableModel modelo = new DefaultTableModel(
        new String[] {"ID", "Cliente", "Producto", "Cantidad", "Precio S/", "Estado"}, 0) {
        @Override public boolean isCellEditable(int row, int column) { return false; }
    };
    private final JTable tabla = new JTable(modelo);
    private final JComboBox<Cliente> clientes = new JComboBox<>();
    private final JComboBox<String> estados = new JComboBox<>(ESTADOS);
    private final JTextField producto = new JTextField();
    private final JTextField cantidad = new JTextField("1");
    private final JTextField precio = new JTextField("12.50");
    private final JLabel estado = new JLabel("Sin conexión · EC2 / RDS");

    private record Cliente(int id, String nombre) {
        @Override public String toString() { return nombre + " (#" + id + ")"; }
    }

    public CafeDesktop() {
        super("VALLE CAFÉ · Control de pedidos");
        setDefaultCloseOperation(DO_NOTHING_ON_CLOSE);
        addWindowListener(new WindowAdapter() {
            @Override public void windowClosing(WindowEvent e) { desconectar(); dispose(); System.exit(0); }
        });
        setSize(1050, 660);
        setLocationRelativeTo(null);
        construirInterfaz();
        SwingUtilities.invokeLater(this::conectar);
    }

    private void construirInterfaz() {
        JPanel raiz = new JPanel(new BorderLayout(16, 16));
        raiz.setBackground(CREMA);
        raiz.setBorder(BorderFactory.createEmptyBorder(20, 24, 24, 24));
        JPanel cabecera = new JPanel(new BorderLayout());
        cabecera.setBackground(VERDE);
        cabecera.setBorder(BorderFactory.createEmptyBorder(22, 25, 22, 25));
        JLabel titulo = new JLabel("☕  VALLE CAFÉ  /  PEDIDOS");
        titulo.setFont(new Font("SansSerif", Font.BOLD, 25));
        titulo.setForeground(Color.WHITE);
        cabecera.add(titulo, BorderLayout.WEST);
        estado.setForeground(new Color(226, 213, 170));
        cabecera.add(estado, BorderLayout.EAST);
        raiz.add(cabecera, BorderLayout.NORTH);

        JPanel contenido = new JPanel(new BorderLayout(14, 14));
        contenido.setOpaque(false);
        JLabel subtitulo = new JLabel("Gestión compartida con Flask + MySQL AWS RDS");
        subtitulo.setFont(new Font("SansSerif", Font.PLAIN, 15));
        contenido.add(subtitulo, BorderLayout.NORTH);
        tabla.setRowHeight(33);
        tabla.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        tabla.getTableHeader().setFont(new Font("SansSerif", Font.BOLD, 13));
        tabla.setFont(new Font("SansSerif", Font.PLAIN, 13));
        contenido.add(new JScrollPane(tabla), BorderLayout.CENTER);
        raiz.add(contenido, BorderLayout.CENTER);

        JPanel pie = new JPanel(new BorderLayout(8, 10));
        pie.setOpaque(false);
        JPanel campos = new JPanel(new GridLayout(2, 5, 10, 5));
        campos.setOpaque(false);
        for (String nombre : new String[] {"Cliente", "Producto", "Cantidad", "Precio unitario (S/)", "Estado"}) {
            JLabel label = new JLabel(nombre);
            label.setForeground(VERDE);
            campos.add(label);
        }
        for (JComponent campo : new JComponent[] {clientes, producto, cantidad, precio, estados}) {
            campo.setFont(new Font("SansSerif", Font.PLAIN, 14));
            campos.add(campo);
        }
        pie.add(campos, BorderLayout.NORTH);
        JPanel acciones = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 4));
        acciones.setOpaque(false);
        boton(acciones, "Conectar / reconectar", this::conectar);
        boton(acciones, "Actualizar lista", this::actualizar);
        boton(acciones, "+ Registrar pedido", this::insertar);
        boton(acciones, "Editar seleccionado", this::editar);
        boton(acciones, "Eliminar seleccionado", this::eliminar);
        boton(acciones, "Limpiar", () -> { tabla.clearSelection(); producto.setText(""); cantidad.setText("1"); precio.setText("12.50"); });
        pie.add(acciones, BorderLayout.SOUTH);
        raiz.add(pie, BorderLayout.SOUTH);
        setContentPane(raiz);
        tabla.getSelectionModel().addListSelectionListener(evento -> {
            if (evento.getValueIsAdjusting() || tabla.getSelectedRow() < 0) return;
            int fila = tabla.convertRowIndexToModel(tabla.getSelectedRow());
            producto.setText(String.valueOf(modelo.getValueAt(fila, 2)));
            cantidad.setText(String.valueOf(modelo.getValueAt(fila, 3)));
            precio.setText(String.valueOf(modelo.getValueAt(fila, 4)));
            estados.setSelectedItem(modelo.getValueAt(fila, 5));
            String nombreCliente = String.valueOf(modelo.getValueAt(fila, 1));
            for (int i = 0; i < clientes.getItemCount(); i++) {
                if (clientes.getItemAt(i).nombre().equals(nombreCliente)) { clientes.setSelectedIndex(i); break; }
            }
        });
    }

    private void boton(JPanel panel, String texto, Runnable accion) {
        JButton boton = new JButton(texto);
        boton.setForeground(VERDE);
        boton.setFocusPainted(false);
        boton.addActionListener(e -> accion.run());
        panel.add(boton);
    }

    private String dato(String clave) {
        String valor = config.getProperty(clave, "").trim();
        if (valor.isEmpty()) throw new IllegalArgumentException("Falta " + clave + " en desktop/config.properties");
        return valor;
    }

    private void conectar() {
        desconectar();
        try (InputStream archivo = Files.newInputStream(Path.of("config.properties"))) {
            config.clear();
            config.load(archivo);
            String password = config.getProperty("db.password", "");
            if (password.isBlank()) {
                JPasswordField entrada = new JPasswordField();
                int respuesta = JOptionPane.showConfirmDialog(this, entrada, "Contraseña MySQL de app_desktop", JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);
                if (respuesta != JOptionPane.OK_OPTION) return;
                char[] caracteres = entrada.getPassword();
                password = new String(caracteres);
                Arrays.fill(caracteres, '\0');
            }
            JSch jsch = new JSch();
            jsch.setKnownHosts(dato("ssh.knownHosts"));
            jsch.addIdentity(dato("ssh.privateKey"));
            sesion = jsch.getSession(dato("ssh.user"), dato("ssh.host"), Integer.parseInt(dato("ssh.port")));
            sesion.setConfig("StrictHostKeyChecking", "yes");
            sesion.connect(12_000);
            int puertoLocal = Integer.parseInt(dato("local.port"));
            sesion.setPortForwardingL("127.0.0.1", puertoLocal, dato("rds.host"), Integer.parseInt(dato("rds.port")));
            // El tráfico MySQL viaja cifrado dentro del túnel; se exige además TLS en JDBC.
            String url = "jdbc:mysql://127.0.0.1:" + puertoLocal + "/" + dato("db.name")
                + "?sslMode=REQUIRED&connectTimeout=9000&socketTimeout=12000";
            conexion = DriverManager.getConnection(url, dato("db.user"), password);
            estado.setText("● CONECTADO · SSH + JDBC");
            actualizar();
        } catch (Exception ex) {
            desconectar();
            error("No se pudo conectar a AWS. Verifica SSH, IP, llave, known_hosts, RDS y credenciales.", ex);
        }
    }

    private void desconectar() {
        try { if (conexion != null) conexion.close(); } catch (SQLException ignored) { }
        conexion = null;
        if (sesion != null) sesion.disconnect();
        sesion = null;
        estado.setText("● SIN CONEXIÓN");
    }

    private boolean disponible() {
        if (conexion != null) return true;
        JOptionPane.showMessageDialog(this, "Primero conecta la aplicación a AWS.");
        return false;
    }

    private void actualizar() {
        if (!disponible()) return;
        try {
            clientes.removeAllItems();
            try (PreparedStatement sql = conexion.prepareStatement("SELECT id, nombre FROM clientes ORDER BY nombre"); ResultSet rs = sql.executeQuery()) {
                while (rs.next()) clientes.addItem(new Cliente(rs.getInt("id"), rs.getString("nombre")));
            }
            modelo.setRowCount(0);
            String consulta = "SELECT p.id,c.nombre,p.producto,p.cantidad,p.precio_unitario,p.estado FROM pedidos p JOIN clientes c ON c.id=p.cliente_id ORDER BY p.id DESC";
            try (PreparedStatement sql = conexion.prepareStatement(consulta); ResultSet rs = sql.executeQuery()) {
                while (rs.next()) modelo.addRow(new Object[] {rs.getInt(1), rs.getString(2), rs.getString(3), rs.getInt(4), rs.getBigDecimal(5), rs.getString(6)});
            }
        } catch (SQLException ex) { error("No se pudieron actualizar los datos.", ex); }
    }

    private List<Object> datosFormulario() {
        Cliente cliente = (Cliente) clientes.getSelectedItem();
        if (cliente == null) throw new IllegalArgumentException("Registra primero un cliente desde la web.");
        String articulo = producto.getText().trim();
        if (articulo.isEmpty() || articulo.length() > 100) throw new IllegalArgumentException("Escribe un producto de hasta 100 caracteres.");
        int unidades = Integer.parseInt(cantidad.getText().trim());
        BigDecimal valor = new BigDecimal(precio.getText().trim());
        if (unidades < 1 || valor.signum() <= 0 || valor.compareTo(new BigDecimal("99999999.99")) > 0) throw new IllegalArgumentException("Cantidad y precio deben ser positivos.");
        return new ArrayList<>(List.of(cliente.id(), articulo, unidades, valor, estados.getSelectedItem()));
    }

    private void insertar() { guardar(false); }
    private void editar() { guardar(true); }

    private void guardar(boolean editar) {
        if (!disponible()) return;
        int fila = tabla.getSelectedRow();
        if (editar && fila < 0) { JOptionPane.showMessageDialog(this, "Selecciona un pedido para editar."); return; }
        try {
            List<Object> valores = datosFormulario();
            if (editar) valores.add(modelo.getValueAt(tabla.convertRowIndexToModel(fila), 0));
            String sql = editar
                ? "UPDATE pedidos SET cliente_id=?,producto=?,cantidad=?,precio_unitario=?,estado=? WHERE id=?"
                : "INSERT INTO pedidos(cliente_id,producto,cantidad,precio_unitario,estado) VALUES (?,?,?,?,?)";
            try (PreparedStatement stmt = conexion.prepareStatement(sql)) {
                for (int i = 0; i < valores.size(); i++) stmt.setObject(i + 1, valores.get(i));
                stmt.executeUpdate();
            }
            actualizar();
            JOptionPane.showMessageDialog(this, editar ? "Pedido actualizado. Refresca la web para comprobarlo." : "Pedido agregado. Refresca la web para comprobarlo.");
        } catch (SQLException | IllegalArgumentException ex) { error("No se pudo guardar el pedido.", ex); }
    }

    private void eliminar() {
        if (!disponible()) return;
        int fila = tabla.getSelectedRow();
        if (fila < 0) { JOptionPane.showMessageDialog(this, "Selecciona un pedido."); return; }
        if (JOptionPane.showConfirmDialog(this, "¿Eliminar definitivamente este pedido?", "Confirmación", JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) return;
        int id = (int) modelo.getValueAt(tabla.convertRowIndexToModel(fila), 0);
        try (PreparedStatement stmt = conexion.prepareStatement("DELETE FROM pedidos WHERE id=?")) {
            stmt.setInt(1, id);
            stmt.executeUpdate();
            actualizar();
        } catch (SQLException ex) { error("No se pudo eliminar el pedido.", ex); }
    }

    private void error(String mensaje, Exception ex) {
        JOptionPane.showMessageDialog(this, mensaje + "\nDetalle: " + ex.getMessage(), "Valle Café", JOptionPane.ERROR_MESSAGE);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new CafeDesktop().setVisible(true));
    }
}
