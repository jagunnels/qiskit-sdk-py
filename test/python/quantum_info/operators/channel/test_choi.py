# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

# pylint: disable=invalid-name,missing-docstring
"""Tests for Choi quantum channel representation class."""

import unittest
import numpy as np

from qiskit import QiskitError
from qiskit.quantum_info.operators.channel import Choi
from .channel_test_case import ChannelTestCase


class TestChoi(ChannelTestCase):
    """Tests for Choi channel representation."""

    def test_init(self):
        """Test initialization"""
        mat4 = np.eye(4) / 2.0
        chan = Choi(mat4)
        self.assertAllClose(chan.data, mat4)
        self.assertEqual(chan.dim, (2, 2))

        mat8 = np.eye(8) / 2.0
        chan = Choi(mat8, input_dims=4)
        self.assertAllClose(chan.data, mat8)
        self.assertEqual(chan.dim, (4, 2))

        chan = Choi(mat8, input_dims=2)
        self.assertAllClose(chan.data, mat8)
        self.assertEqual(chan.dim, (2, 4))

        mat16 = np.eye(16) / 4
        chan = Choi(mat16)
        self.assertAllClose(chan.data, mat16)
        self.assertEqual(chan.dim, (4, 4))

        # Wrong input or output dims should raise exception
        self.assertRaises(
            QiskitError, Choi, mat8, input_dims=[4], output_dims=[4])

    def test_equal(self):
        """Test __eq__ method"""
        mat = self.rand_matrix(4, 4)
        self.assertEqual(Choi(mat), Choi(mat))

    def test_copy(self):
        """Test copy method"""
        mat = np.eye(4)
        orig = Choi(mat)
        cpy = orig.copy()
        cpy._data[0, 0] = 0.0
        self.assertFalse(cpy == orig)

    def test_evolve(self):
        """Test evolve method."""
        input_psi = [0, 1]
        input_rho = [[0, 0], [0, 1]]
        # Identity channel
        chan = Choi(self.choiI)
        target_rho = np.array([[0, 0], [0, 1]])
        self.assertAllClose(chan._evolve(input_psi), target_rho)
        self.assertAllClose(chan._evolve(np.array(input_psi)), target_rho)
        self.assertAllClose(chan._evolve(input_rho), target_rho)
        self.assertAllClose(chan._evolve(np.array(input_rho)), target_rho)

        # Hadamard channel
        chan = Choi(self.choiH)
        target_rho = np.array([[1, -1], [-1, 1]]) / 2
        self.assertAllClose(chan._evolve(input_psi), target_rho)
        self.assertAllClose(chan._evolve(np.array(input_psi)), target_rho)
        self.assertAllClose(chan._evolve(input_rho), target_rho)
        self.assertAllClose(chan._evolve(np.array(input_rho)), target_rho)

        # Completely depolarizing channel
        chan = Choi(self.depol_choi(1))
        target_rho = np.eye(2) / 2
        self.assertAllClose(chan._evolve(input_psi), target_rho)
        self.assertAllClose(chan._evolve(np.array(input_psi)), target_rho)
        self.assertAllClose(chan._evolve(input_rho), target_rho)
        self.assertAllClose(chan._evolve(np.array(input_rho)), target_rho)

    def test_is_cptp(self):
        """Test is_cptp method."""
        self.assertTrue(Choi(self.depol_choi(0.25)).is_cptp())
        # Non-CPTP should return false
        self.assertFalse(
            Choi(1.25 * self.choiI - 0.25 * self.depol_choi(1)).is_cptp())

    def test_conjugate(self):
        """Test conjugate method."""
        # Test channel measures in Z basis and prepares in Y basis
        # Zp -> Yp, Zm -> Ym
        Zp, Zm = np.diag([1, 0]), np.diag([0, 1])
        Yp, Ym = np.array([[1, -1j], [1j, 1]]) / 2, np.array([[1, 1j],
                                                              [-1j, 1]]) / 2
        chan = Choi(np.kron(Zp, Yp) + np.kron(Zm, Ym))
        # Conjugate channel swaps Y-basis states
        targ = Choi(np.kron(Zp, Ym) + np.kron(Zm, Yp))
        chan_conj = chan.conjugate()
        self.assertEqual(chan_conj, targ)

    def test_transpose(self):
        """Test transpose method."""
        # Test channel measures in Z basis and prepares in Y basis
        # Zp -> Yp, Zm -> Ym
        Zp, Zm = np.diag([1, 0]), np.diag([0, 1])
        Yp, Ym = np.array([[1, -1j], [1j, 1]]) / 2, np.array([[1, 1j],
                                                              [-1j, 1]]) / 2
        chan = Choi(np.kron(Zp, Yp) + np.kron(Zm, Ym))
        # Transpose channel swaps basis
        targ = Choi(np.kron(Yp, Zp) + np.kron(Ym, Zm))
        chan_t = chan.transpose()
        self.assertEqual(chan_t, targ)

    def test_adjoint(self):
        """Test adjoint method."""
        # Test channel measures in Z basis and prepares in Y basis
        # Zp -> Yp, Zm -> Ym
        Zp, Zm = np.diag([1, 0]), np.diag([0, 1])
        Yp, Ym = np.array([[1, -1j], [1j, 1]]) / 2, np.array([[1, 1j],
                                                              [-1j, 1]]) / 2
        chan = Choi(np.kron(Zp, Yp) + np.kron(Zm, Ym))
        # Ajoint channel swaps Y-basis elements abd Z<->Y bases
        targ = Choi(np.kron(Ym, Zp) + np.kron(Yp, Zm))
        chan_adj = chan.adjoint()
        self.assertEqual(chan_adj, targ)

    def test_compose_except(self):
        """Test compose different dimension exception"""
        self.assertRaises(QiskitError,
                          Choi(np.eye(4)).compose, Choi(np.eye(8)))
        self.assertRaises(QiskitError, Choi(np.eye(4)).compose, 2)

    def test_compose(self):
        """Test compose method."""
        # UnitaryChannel evolution
        chan1 = Choi(self.choiX)
        chan2 = Choi(self.choiY)
        chan = chan1.compose(chan2)
        targ = Choi(self.choiZ)
        self.assertEqual(chan, targ)

        # 50% depolarizing channel
        chan1 = Choi(self.depol_choi(0.5))
        chan = chan1.compose(chan1)
        targ = Choi(self.depol_choi(0.75))
        self.assertEqual(chan, targ)

        # Measure and rotation
        Zp, Zm = np.diag([1, 0]), np.diag([0, 1])
        Xp, Xm = np.array([[1, 1], [1, 1]]) / 2, np.array([[1, -1], [-1, 1]
                                                           ]) / 2
        chan1 = Choi(np.kron(Zp, Xp) + np.kron(Zm, Xm))
        chan2 = Choi(self.choiX)
        # X-gate second does nothing
        targ = Choi(np.kron(Zp, Xp) + np.kron(Zm, Xm))
        self.assertEqual(chan1.compose(chan2), targ)
        self.assertEqual(chan1 @ chan2, targ)
        # X-gate first swaps Z states
        targ = Choi(np.kron(Zm, Xp) + np.kron(Zp, Xm))
        self.assertEqual(chan2.compose(chan1), targ)
        self.assertEqual(chan2 @ chan1, targ)

        # Compose different dimensions
        chan1 = Choi(np.eye(8) / 4, input_dims=2, output_dims=4)
        chan2 = Choi(np.eye(8) / 2, input_dims=4, output_dims=2)
        chan = chan1.compose(chan2)
        self.assertEqual(chan.dim, (2, 2))
        chan = chan2.compose(chan1)
        self.assertEqual(chan.dim, (4, 4))

    def test_compose_front(self):
        """Test front compose method."""
        # UnitaryChannel evolution
        chan1 = Choi(self.choiX)
        chan2 = Choi(self.choiY)
        chan = chan1.compose(chan2, front=True)
        targ = Choi(self.choiZ)
        self.assertEqual(chan, targ)

        # 50% depolarizing channel
        chan1 = Choi(self.depol_choi(0.5))
        chan = chan1.compose(chan1, front=True)
        targ = Choi(self.depol_choi(0.75))
        self.assertEqual(chan, targ)

        # Measure and rotation
        Zp, Zm = np.diag([1, 0]), np.diag([0, 1])
        Xp, Xm = np.array([[1, 1], [1, 1]]) / 2, np.array([[1, -1], [-1, 1]
                                                           ]) / 2
        chan1 = Choi(np.kron(Zp, Xp) + np.kron(Zm, Xm))
        chan2 = Choi(self.choiX)
        # X-gate second does nothing
        chan = chan2.compose(chan1, front=True)
        targ = Choi(np.kron(Zp, Xp) + np.kron(Zm, Xm))
        self.assertEqual(chan, targ)
        # X-gate first swaps Z states
        chan = chan1.compose(chan2, front=True)
        targ = Choi(np.kron(Zm, Xp) + np.kron(Zp, Xm))
        self.assertEqual(chan, targ)

        # Compose different dimensions
        chan1 = Choi(np.eye(8) / 4, input_dims=2, output_dims=4)
        chan2 = Choi(np.eye(8) / 2, input_dims=4, output_dims=2)
        chan = chan1.compose(chan2, front=True)
        self.assertEqual(chan.dim, (4, 4))
        chan = chan2.compose(chan1, front=True)
        self.assertEqual(chan.dim, (2, 2))

    def test_expand(self):
        """Test expand method."""
        rho0, rho1 = np.diag([1, 0]), np.diag([0, 1])
        rho_init = np.kron(rho0, rho0)
        chan1 = Choi(self.choiI)
        chan2 = Choi(self.choiX)

        # X \otimes I
        chan = chan1.expand(chan2)
        rho_targ = np.kron(rho1, rho0)
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)

        # I \otimes X
        chan = chan2.expand(chan1)
        rho_targ = np.kron(rho0, rho1)
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)

        # Completely depolarizing
        chan_dep = Choi(self.depol_choi(1))
        chan = chan_dep.expand(chan_dep)
        rho_targ = np.diag([1, 1, 1, 1]) / 4
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)

    def test_tensor(self):
        """Test tensor method."""
        rho0, rho1 = np.diag([1, 0]), np.diag([0, 1])
        rho_init = np.kron(rho0, rho0)
        chan1 = Choi(self.choiI)
        chan2 = Choi(self.choiX)

        # X \otimes I
        rho_targ = np.kron(rho1, rho0)
        chan = chan2.tensor(chan1)
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)
        chan = chan2 ^ chan1
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)

        # I \otimes X
        rho_targ = np.kron(rho0, rho1)
        chan = chan1.tensor(chan2)
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)
        chan = chan1 ^ chan2
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)

        # Completely depolarizing
        rho_targ = np.diag([1, 1, 1, 1]) / 4
        chan_dep = Choi(self.depol_choi(1))
        chan = chan_dep.tensor(chan_dep)
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)
        chan = chan_dep ^ chan_dep
        self.assertEqual(chan.dim, (4, 4))
        self.assertAllClose(chan._evolve(rho_init), rho_targ)

    def test_power(self):
        """Test power method."""
        # 10% depolarizing channel
        p_id = 0.9
        depol = Choi(self.depol_choi(1 - p_id))

        # Compose 3 times
        p_id3 = p_id**3
        chan3 = depol.power(3)
        targ3 = Choi(self.depol_choi(1 - p_id3))
        self.assertEqual(chan3, targ3)

    def test_power_except(self):
        """Test power method raises exceptions."""
        chan = Choi(self.depol_choi(1))
        # Non-integer power raises error
        self.assertRaises(QiskitError, chan.power, 0.5)

    def test_add(self):
        """Test add method."""
        mat1 = 0.5 * self.choiI
        mat2 = 0.5 * self.depol_choi(1)
        targ = Choi(mat1 + mat2)

        chan1 = Choi(mat1)
        chan2 = Choi(mat2)
        self.assertEqual(chan1.add(chan2), targ)
        self.assertEqual(chan1 + chan2, targ)

    def test_add_except(self):
        """Test add method raises exceptions."""
        chan1 = Choi(self.choiI)
        chan2 = Choi(np.eye(8))
        self.assertRaises(QiskitError, chan1.add, chan2)
        self.assertRaises(QiskitError, chan1.add, 5)

    def test_subtract(self):
        """Test subtract method."""
        mat1 = 0.5 * self.choiI
        mat2 = 0.5 * self.depol_choi(1)
        targ = Choi(mat1 - mat2)

        chan1 = Choi(mat1)
        chan2 = Choi(mat2)
        self.assertEqual(chan1.subtract(chan2), targ)
        self.assertEqual(chan1 - chan2, targ)

    def test_subtract_except(self):
        """Test subtract method raises exceptions."""
        chan1 = Choi(self.choiI)
        chan2 = Choi(np.eye(8))
        self.assertRaises(QiskitError, chan1.subtract, chan2)
        self.assertRaises(QiskitError, chan1.subtract, 5)

    def test_multiply(self):
        """Test multiply method."""
        chan = Choi(self.choiI)
        val = 0.5
        targ = Choi(val * self.choiI)
        self.assertEqual(chan.multiply(val), targ)
        self.assertEqual(val * chan, targ)
        self.assertEqual(chan * val, targ)

    def test_multiply_except(self):
        """Test multiply method raises exceptions."""
        chan = Choi(self.choiI)
        self.assertRaises(QiskitError, chan.multiply, 's')
        self.assertRaises(QiskitError, chan.multiply, chan)

    def test_negate(self):
        """Test negate method"""
        chan = Choi(self.choiI)
        targ = Choi(-1 * self.choiI)
        self.assertEqual(-chan, targ)


if __name__ == '__main__':
    unittest.main()
