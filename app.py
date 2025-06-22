from flask import Flask, request, jsonify
from math import factorial

app = Flask(__name__)

def calcular_p0(lambd, mu, c):
    rho = lambd / (c * mu)
    sumatoria = sum((lambd / mu) ** n / factorial(n) for n in range(c))
    ultimo_termino = ((lambd / mu) ** c) / (factorial(c) * (1 - rho))
    p0 = 1 / (sumatoria + ultimo_termino)
    return p0

def calcular_metricas(lambd, mu, c):
    rho = lambd / (c * mu)
    if rho >= 1:
        return {"error": "El sistema no es estable. Rho debe ser menor a 1."}
    p0 = calcular_p0(lambd, mu, c)
    lq = (p0 * ((lambd / mu) ** c) * rho) / (factorial(c) * (1 - rho) ** 2)
    wq = lq / lambd
    w = wq + (1 / mu)
    l = lambd * w

    return {
        "lambda": lambd,
        "mu": mu,
        "c": c,
        "rho": round(rho, 4),
        "p0": round(p0, 4),
        "Lq": round(lq, 4),
        "Wq": round(wq * 60, 2),
        "W": round(w * 60, 2),
        "L": round(l, 4),
        "recomendacion": generar_recomendacion(rho)
    }

def calcular_optimo_servidores(lambd, tiempo_servicio, costo_espera_por_cliente, costo_por_servidor):
    mu = 60 / tiempo_servicio
    resultados = []
    for c in range(1, 21):
        rho = lambd / (c * mu)
        if rho >= 1:
            continue
        p0 = calcular_p0(lambd, mu, c)
        lq = (p0 * ((lambd / mu) ** c) * rho) / (factorial(c) * (1 - rho) ** 2)
        wq = lq / lambd
        costo_total = (wq * costo_espera_por_cliente * lambd) + (c * costo_por_servidor)
        resultados.append({
            "servidores": c,
            "Lq": round(lq, 2),
            "Wq": round(wq * 60, 2),
            "rho": round(rho, 4),
            "costo_total": round(costo_total, 2)
        })

    if not resultados:
        return {"error": "No se encontró un número de servidores que estabilice el sistema."}

    optimo = min(resultados, key=lambda x: x["costo_total"])
    return {
        "optimo": optimo,
        "todas_las_opciones": resultados
    }

def generar_recomendacion(rho):
    if rho < 0.7:
        return "El sistema está bien dimensionado."
    elif rho < 0.85:
        return "El sistema está ocupado, pero aún dentro de límites aceptables."
    else:
        return "El sistema está sobrecargado. Considere aumentar el número de servidores."

# RUTA 1: Calcular métricas del sistema
@app.route('/api/colas', methods=['POST'])
def api_colas():
    try:
        data = request.json
        lambd = float(data["tasa_llegada"])
        tiempo_servicio = float(data["tiempo_servicio"])
        c = int(data["servidores"])

        if lambd <= 0 or tiempo_servicio <= 0 or c <= 0:
            raise ValueError("Todos los valores deben ser mayores que cero.")
        
        mu = 60 / tiempo_servicio
        return jsonify(calcular_metricas(lambd, mu, c))

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# RUTA 2: Calcular número óptimo de empleados
@app.route('/api/colas/optimo', methods=['POST'])
def api_optimo():
    try:
        data = request.json
        lambd = float(data["tasa_llegada"])
        tiempo_servicio = float(data["tiempo_servicio"])
        costo_espera = float(data["costo_espera"])
        costo_servidor = float(data["costo_servidor"])

        if lambd <= 0 or tiempo_servicio <= 0 or costo_espera < 0 or costo_servidor < 0:
            raise ValueError("Los valores deben ser mayores que cero.")
        
        return jsonify(calcular_optimo_servidores(lambd, tiempo_servicio, costo_espera, costo_servidor))

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
