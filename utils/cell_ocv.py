# -*- coding: utf-8 -*-

"""
Adaption of OCV-relaxation data.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


class Cell(object):
    """
    This class will read observed data and plot fitted observed data.
    It will also calculate theoretical ocv relaxation behavior based on given
    information about the cell.
    """

    def __init__(self, time, voltage, v_start, i_start, contribute, slope):
        """
        :param time: array with measured time values
        :param voltage: array with measured voltage values
        :param v_start: voltage when t < 0 (right before OC and IR drop happen)
        :param i_start: current calculated with mass, c_cap, c_rate. Current
        through circuit at t = 0
        :param contribute: 0 <= contribute <= 1 where 0 is no contribution to
        relaxation voltage (v_rlx) from the charge-transfer.
        1 when charge-transfer rc-circuit is the only contributor to v_rlx
        :param slope: the slope of the time constant if not constant
        :type time: np.array
        :type voltage: np.array
        :type v_start: float
        :type i_start: float
        :type contribute: float
        :type slope: dict
        :key slope: {'d', 'ct'}
        """
        self._time = time
        self._voltage = voltage
        self._v_cut = v_start   # Before IR-drop, cut-off voltage
        self._i_cut = i_start   # current before cut-off. Will make IR-drop
        # self._c_cap = c_cap   # used outside of class to calculate i_start
        # =self._i_cut
        # self._c_rate = c_rate
        self._contribute = contribute
        if not slope:
            self._slope = {'d': None, 'ct': None}
        else:
            self._slope = slope

        self.ocv = self._voltage[-1]
        self.v_0 = self._voltage[0]  # self._v_start - self._v_ir   # After
        # IR-drop (over v_ct + v_d + ocv)
        self._v_rlx = self.v_0 - self.ocv   # This is the relaxation curve
        # over v_ct + v_d
        self.v_ir = abs(self._v_cut - self.v_0)   # cut-off voltage - v_0
        self.r_ir = self.v_ir / self._i_cut
        # self._r_ct = self._v_ct / self._i_cut   # v_ct = f(v_rlx)(= v_rlx * x)
        # self._r_d = self._v_d / self._i_cut   # v_d = f(v_rlx)

        # defining parameters
        self.v_ct = None
        self.v_d = None
        self.r_ct = None
        self.r_d = None
        self.c_ct = None
        self.c_d = None
        self.v_ct_0 = None
        self.v_d_0 = None

    def tau(self, v_rc_0, v_rc, r, c, slope):
        """
        Calculate the time constant based on which resistance and capacitance
        it receives.
        :param slope: slope of the time constant [s]
        :param r: resistance [Ohm]
        :param c: capacity [F]
        :return: self._slope * self._time + r * c
        """
        if slope:
            return slope * self._time + abs(self._time[-1] /
            math.log(v_rc_0/v_rc[-1]))
            # return slope * self._time + r * c
        else:
            return abs(self._time[-1] / math.log(v_rc_0/v_rc[-1]))
            # return r * c

    def guessing_parameters(self):
        """
        Guessing likely parameters that will fit best to the measured data.
        These guessed parameters are to be used when fitting a curve to
        measured data.
        :return: None
        """
        # Say we know v_0 (after IR-drop). We also know C_cap and C_rate (
        # whatever they are). I have to assume that the charge-transfer rate
        # is 0.2 times the voltage across the relaxation circuits (0.2 is an
        # example of what self._contribute is guessed to be). So 0.2 *
        # self._v_rlx (which is self.v_0 - self.ocv. This means that 1-0.2 =
        #  0.8 times v_rlx is from the diffusion part.
        self.v_ct = self._v_rlx * self._contribute
        self.v_d = self._v_rlx * (1 - self._contribute)
        self.r_ct = self.v_ct / self._i_cut
        self.r_d = self.v_d / self._i_cut
        # alt.
        # self.r_d = self.v_cut / self.i_cut - self.r_ct - self.r_ir

        self.v_ct_0 = self.v_0 * (self.r_ct / (self.r_ct + self.r_d))
        self.v_d_0 = self.v_0 * (self.r_d / (self.r_ct + self.r_d))

        tau_ct = self.tau(self.v_ct_0, self.v_ct, None, None, self._slope['ct'])
        tau_d = self.tau(self.v_d_0, self.v_d, None, None, self._slope['d'])
        self.c_ct = tau_ct / self.r_ct
        self.c_d = tau_d / self.r_d

    def relaxation_rc(self, v0, r, c, slope):
        """
        Calculate the relaxation function with a np.array of time, self._time
        Make a local constant, modify (for modifying a rc-circuit so that
        guessing is easier).
        modify = -self._start_volt * exp(-1. / self._slope)
        if self._slope of self.tau() is 0, then -exp(-1./self._slope) = 0
        :param v0: the initial voltage across the rc-circuit at t = 0,
        i.e. v_ct_0
        :param r: the resistance over the rc-circuit
        :param c: the capacitance over the rc-circuit
        :param slope: the slope of the time constant in the rc-circuit
        :return: start_volt(modify + exp(-self._time / self.tau()))
        :type: Numpy array with relax data with same length as self._time
        """
        if slope:
            modify = -self.v_0 * math.exp(-1. / slope)
        else:
            modify = 0
        return v0 * (modify + math.exp(-self._time
                                       / self.tau(None, None,  r, c, slope)))

    def ocv_relax_func(self):
        """
        To use self.relaxation_rc() for calculating complete ocv relaxation
        over the cell. Guessing parameters
        :return: self.v_0 =  voltage_d + voltage_ct + voltage_ocv
        """
        # This is self.v_d
        voltage_d = self.relaxation_rc(self.v_d_0, self.r_d, self.c_d,
                                       self._slope['d'])
        # This is self.v_ct
        voltage_ct = self.relaxation_rc(self.v_ct_0, self.r_ct, self.c_ct,
                                        self._slope['ct'])
        # basically return the same as self.v_0 is suppose to be...
        return voltage_d + voltage_ct + self.ocv
