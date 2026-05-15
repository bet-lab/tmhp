"""
Unit conversion utilities and conversion constants.

This module provides temperature conversion functions and a comprehensive
set of unit conversion multipliers organized by physical dimension.

Categories:
    1. Temperature Conversion Functions — K2C, C2K, F2C, C2F
    2. Time Conversion Constants
    3. Length Conversion Constants
    4. Area Conversion Constants
    5. Volume Conversion Constants
    6. Mass Conversion Constants
    7. Energy Conversion Constants
    8. Power Conversion Constants
    9. Pressure Conversion Constants
   10. Angle Conversion Constants

Usage:
    All constants follow the naming pattern ``<from_unit>2<to_unit>``,
    e.g. ``h2s = 3600`` converts hours to seconds.
"""

import math

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Temperature Conversion Functions
# ═══════════════════════════════════════════════════════════════════════════════


def K2C(K):
    """Convert Kelvin to Celsius."""
    return K - 273.15


def C2K(C):
    """Convert Celsius to Kelvin."""
    return C + 273.15


def F2C(F):
    """Convert Fahrenheit to Celsius."""
    return (F - 32) * 5 / 9


def C2F(C):
    """Convert Celsius to Fahrenheit."""
    return C * 9 / 5 + 32


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Time Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Day
d2h = 24
d2m = 24 * 60
d2s = 24 * 60 * 60
h2d = 1 / 24
m2d = 1 / (24 * 60)
s2d = 1 / (24 * 60 * 60)

# Hour
h2m = 60
h2s = 3600
m2h = 1 / 60
s2h = 1 / 3600

# Minute
m2s = 60
s2m = 1 / 60

# Year
y2d = 365
d2y = 1 / 365


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Length Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

m2cm = 100
cm2m = 1 / 100
m2mm = 1e3
mm2m = 1e-3
m2km = 1e-3
km2m = 1e3
cm2mm = 10
mm2cm = 1 / 10
in2cm = 2.54
cm2in = 1 / 2.54
ft2m = 0.3048
m2ft = 1 / 0.3048


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Area Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

m22cm2 = 1e4
cm22m2 = 1e-4
m22mm2 = 1e6
mm22m2 = 1e-6


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Volume Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

m32cm3 = 1e6
cm32m3 = 1e-6
m32L = 1e3
L2m3 = 1e-3


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Mass Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

kg2g = 1e3
g2kg = 1e-3
kg2mg = 1e6
mg2kg = 1e-6
kg2t = 1e-3
t2kg = 1e3


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Energy Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

J2kJ = 1e-3
kJ2J = 1e3
J2MJ = 1e-6
MJ2J = 1e6
J2GJ = 1e-9
GJ2J = 1e9
kWh2J = 3.6e6
J2kWh = 1 / 3.6e6
Btu2J = 1055.06
J2Btu = 1 / 1055.06


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Power Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

W2kW = 1e-3
W2MW = 1e-6
W2GW = 1e-9

kW2W = 1e3
MW2W = 1e6
W2mW = 1e3
mW2W = 1e-3


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Pressure Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

Pa2kPa = 1e-3
kPa2Pa = 1e3
Pa2MPa = 1e-6
MPa2Pa = 1e6
Pa2bar = 1e-5
bar2Pa = 1e5
atm2Pa = 101325
Pa2atm = 1 / 101325


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Angle Conversion Constants
# ═══════════════════════════════════════════════════════════════════════════════

d2r = math.pi / 180
r2d = 180 / math.pi
