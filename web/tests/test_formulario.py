"""Pruebas de validación que no necesitan un RDS activo."""
from decimal import Decimal
import unittest
from werkzeug.datastructures import MultiDict

from app import leer_pedido


class FormularioTests(unittest.TestCase):
    def test_pedido_valido(self):
        datos = leer_pedido(MultiDict({
            'cliente_id': '1', 'producto': 'Latte Vainilla',
            'cantidad': '2', 'precio_unitario': '13.50', 'estado': 'Pendiente'}))
        self.assertEqual(datos, (1, 'Latte Vainilla', 2, Decimal('13.50'), 'Pendiente'))

    def test_precio_negativo(self):
        with self.assertRaises(ValueError):
            leer_pedido(MultiDict({'cliente_id': '1', 'producto': 'Mocha',
                                    'cantidad': '1', 'precio_unitario': '-2', 'estado': 'Listo'}))

    def test_estado_invalido(self):
        with self.assertRaises(ValueError):
            leer_pedido(MultiDict({'cliente_id': '1', 'producto': 'Mocha',
                                    'cantidad': '1', 'precio_unitario': '5', 'estado': 'Falso'}))


if __name__ == '__main__':
    unittest.main()
