# -*- coding: utf-8 -*-
"""
Created on Mon Sep 29 18:05:56 2025

@author: PE48310640
"""
# ejemplo_gr4j.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import differential_evolution

# ---------------------------
# Función GR4J en Python
# ---------------------------
def gr4j_run(P, E, X1, X2, X3, X4, S0=None, R0=None):
    P = np.asarray(P, dtype=float)
    E = np.asarray(E, dtype=float)
    n = len(P)
    if S0 is None: S_prev = X1 * 0.5
    else: S_prev = S0
    if R0 is None: R_prev = X3 * 0.5
    else: R_prev = R0

    Qsim = np.zeros(n)
    for t in range(n):
        p = P[t]
        e = E[t]
        if p >= e:
            Pn = p - e
            En = 0.0
        else:
            Pn = 0.0
            En = e - p

        if Pn > 0:
            added = X1 * (1 - 1 / (1 + Pn / (X1 + 1e-12)))
            added = min(added, Pn)
            S_now = min(X1, S_prev + added)
            runoff_total = Pn - added
        else:
            extracted = min(En, S_prev)
            S_now = max(0.0, S_prev - extracted)
            runoff_total = 0.0

        q_quick = 0.1 * runoff_total
        q_slow = 0.9 * runoff_total + X2

        R_now = min(R_prev + q_slow, X3)
        Rout = R_now / (X4 + 1.0)
        R_now = max(0.0, R_now - Rout)

        Q_total = Rout + q_quick
        Qsim[t] = Q_total

        S_prev = S_now
        R_prev = R_now
    return Qsim

# ---------------------------
# Funciones de calibración
# ---------------------------
def nse(Qobs, Qsim):
    mask = ~np.isnan(Qobs)
    if mask.sum() == 0:
        return -np.inf
    return 1 - np.sum((Qobs[mask]-Qsim[mask])**2) / np.sum((Qobs[mask]-np.mean(Qobs[mask]))**2)

def objective(params, P, E, Qobs):
    Qsim = gr4j_run(P, E, *params)
    return -nse(Qobs, Qsim)  # minimizar

# ---------------------------
# 1) Leer archivo
# ---------------------------
df = pd.read_excel("QNTULUMAYO_diario.xlsx", parse_dates=["Fecha"])
df = df.sort_values("Fecha").reset_index(drop=True)

P = df["P"].values
E = df["E"].values
Qobs = df["Q"].values

# ---------------------------
# 2) Separar calibración y validación
# ---------------------------
split_date = pd.to_datetime("2015-01-01")
mask_cal = df["Fecha"] < split_date
mask_val = df["Fecha"] >= split_date

P_cal, E_cal, Q_cal = P[mask_cal], E[mask_cal], Qobs[mask_cal]
P_val, E_val, Q_val = P[mask_val], E[mask_val], Qobs[mask_val]

# ---------------------------
# 3) Calibración
# ---------------------------
bounds = [(50, 2500), (-5, 5), (20, 500), (1, 20)]  # rangos típicos GR4J
result = differential_evolution(objective, bounds, args=(P_cal, E_cal, Q_cal),
                                maxiter=40, popsize=15, seed=123)
params_opt = result.x
print("Parámetros calibrados:", params_opt)

# ---------------------------
# 4) Simulación con parámetros calibrados
# ---------------------------
Qsim_all = gr4j_run(P, E, *params_opt)
df["Qsim"] = Qsim_all

print("NSE calibración:", nse(Q_cal, gr4j_run(P_cal, E_cal, *params_opt)))
print("NSE validación:", nse(Q_val, gr4j_run(P_val, E_val, *params_opt)))

# ---------------------------
# 5) Exportar resultados
# ---------------------------
df_out = df[["Fecha","P","E","Q","Qsim"]]
df_out.to_excel("Resultados_GR4J.xlsx", index=False)
print("Resultados exportados a Resultados_GR4J.xlsx")

# ---------------------------
# 6) Graficar últimos 2 años
# ---------------------------
last_date = df["Fecha"].max()
mask_last2y = df["Fecha"] >= (last_date - pd.DateOffset(years=2))
df_plot = df[mask_last2y]

plt.figure(figsize=(12,6))
plt.plot(df_plot["Fecha"], df_plot["Q"], label="Qobs", color="black")
plt.plot(df_plot["Fecha"], df_plot["Qsim"], label="Qsim", color="blue")
plt.title("Caudal observado vs simulado (últimos 2 años)")
plt.xlabel("Fecha")
plt.ylabel("Caudal [mm/día]")
plt.legend()
plt.grid(True)
plt.show()

