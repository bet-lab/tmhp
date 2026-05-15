"""TDMA (Tri-Diagonal Matrix Algorithm) solver and related utilities.

Provides:
- ``TDMA``: solve tri-diagonal systems via matrix inversion
- ``_add_loop_advection_terms``: inject forced-convection advection
  terms into TDMA coefficient arrays
"""

import numpy as np


def TDMA(a, b, c, d):
    """
    Solve tri-diagonal matrix system using TDMA (Tri-Diagonal Matrix Algorithm).

    Reference: https://doi.org/10.1016/j.ijheatmasstransfer.2017.09.057 [Appendix B - Eq.(B7)]

    Parameters
    ----------
    a : np.ndarray
        Lower diagonal elements (length N-1)
    b : np.ndarray
        Main diagonal elements (length N)
    c : np.ndarray
        Upper diagonal elements (length N-1)
    d : np.ndarray
        Right-hand side vector (length N)

    Returns
    -------
    np.ndarray
        Solution vector (next time step temperatures)

    Notes
    -----
    If boundary conditions are not None, additional thermal resistances
    are added to the leftmost and rightmost columns, and surface temperatures
    are recalculated considering boundary layer thermal resistance.
    """
    n = len(b)

    A_mat = np.zeros((n, n))
    np.fill_diagonal(A_mat[1:], a[1:])
    np.fill_diagonal(A_mat, b)
    np.fill_diagonal(A_mat[:, 1:], c[:-1])
    A_inv = np.linalg.inv(A_mat)

    T_new = np.dot(A_inv, d).flatten()  # Flatten the result to 1D array
    return T_new


def _add_loop_advection_terms(a, b, c, d, in_idx, out_idx, G_loop, T_loop_in):
    """
    Add forced convection terms for a specified range (in_idx -> out_idx) to TDMA coefficients.

    Indices are 0-based (node 1 -> idx 0).
    Direction: in_idx > out_idx means 'upward' (bottom→top), otherwise 'downward' (top→bottom).

    Parameters
    ----------
    a, b, c, d : np.ndarray
        TDMA coefficient arrays (modified in-place)
    in_idx : int
        Inlet node index (0-based)
    out_idx : int
        Outlet node index (0-based)
    G_loop : float
        Heat capacity flow rate [W/K]
    T_loop_in : float
        Inlet stream temperature [K]

    Notes
    -----
    This function modifies the TDMA coefficients to account for directed advection
    across a node range in either direction.
    """
    # Invalid case: ignore
    if G_loop <= 0 or in_idx == out_idx:
        print("Warning: negative loop flow rate or identical in/out loop nodes.")
        return

    # Inlet node (common)
    b[in_idx] += G_loop
    d[in_idx] += G_loop * T_loop_in  # Inlet stream temperature

    # Upward: in(N side) -> ... -> out(1 side)
    if in_idx > out_idx:
        # Internal nodes in path (out_idx+1 .. in_idx-1)
        for k in range(in_idx - 1, out_idx, -1):
            b[k] += G_loop
            c[k] -= G_loop
        # Outlet node (out_idx)
        b[out_idx] += G_loop
        c[out_idx] -= G_loop

    # Downward: in(1 side) -> ... -> out(N side)
    else:
        for k in range(in_idx + 1, out_idx):
            a[k] -= G_loop
            b[k] += G_loop
        # Outlet node (out_idx)
        a[out_idx] -= G_loop
        b[out_idx] += G_loop
