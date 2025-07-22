# app/services/scania_vehicles_status/service.py
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.scania_vehicles_status.client import vehicle_status_client
from app.services.scania_vehicles_status.evaluation_client import evaluation_client
from app.services.scania_vehicles_status.schemas import (
    VehicleHistoricalData,
    VehicleSummaryData,
)

# ----------------------------------------------------------------------
TANK_CAPACITY_LTS = 105.0        # capacidad fija del depósito AdBlue
# ----------------------------------------------------------------------


async def get_vehicle_historical_data(
    vin: str,
    starttime: str,
    stoptime: str,
) -> Dict[str, Any]:
    """Histórico + resumen.  Calcula litros de AdBlue consumidos
    asumiendo un tanque de 105 L y tomando únicamente las caídas
    de nivel (las subidas ≃ recarga y no computan)."""
    # ── 1. Obtiene el histórico ──────────────────────────────────────
    response = await vehicle_status_client.get_vehicle_status(
        vin=vin,
        starttime=starttime,
        stoptime=stoptime,
        content_filter="HEADER,SNAPSHOT,ACCUMULATED",
        latest_only=False,
    )
    statuses: List[dict] = (
        response.get("vehicleStatusResponse", {}).get("vehicleStatuses", [])
    )

    # ── 2. Recorre y arma lista ordenada ─────────────────────────────
    historico: list[VehicleHistoricalData] = []
    serie_adblue: list[tuple[datetime, float | None]] = []

    for st in statuses:
        ts_raw = st.get("createdDateTime")
        if not ts_raw:
            continue
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))

        km = st.get("hrTotalVehicleDistance", 0) / 1_000.0

        diesel = (
            st["engineTotalFuelUsed"] / 1_000.0
            if st.get("engineTotalFuelUsed") is not None
            else None
        )

        adblue_raw = None
        snap = st.get("snapshotData")
        if snap and "catalystFuelLevel" in snap:
            adblue_raw = snap["catalystFuelLevel"]  # % ó L según ECU

        serie_adblue.append((ts, adblue_raw))

        historico.append(
            VehicleHistoricalData(
                vin=vin,
                timestamp=ts,
                km_recorridos=km,
                consumo_lts_diesel=diesel,
                lts_adblue_consumidos=adblue_raw
            )
        )

    # ── 3. Calcula litros consumidos ─────────────────────────────────
    serie_adblue.sort(key=lambda x: x[0])  # ordena por fecha

    adblue_consumido = 0.0
    previo: float | None = None

    for _, nivel in serie_adblue:
        if nivel is None:
            previo = None
            continue

        # Si la ECU da porcentaje (<=100) lo convertimos a litros
        nivel_lts = (
            nivel * TANK_CAPACITY_LTS / 100
            if nivel <= 100
            else nivel
        )

        if previo is not None and nivel_lts < previo:   # sólo caídas
            adblue_consumido += previo - nivel_lts

        # Si sube ⇒ ­recarga, no suma
        previo = nivel_lts

    adblue_consumido = round(adblue_consumido, 2)

    # ── 4. Datos de Vehicle Evaluation ───────────────────────────────
    eval_distance: float | None = None
    eval_fuel: float | None = None
    try:
        start_dt = datetime.fromisoformat(starttime.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(stoptime.replace("Z", "+00:00"))
        evaluation = await evaluation_client.get_evaluation(
            vin=vin,
            start_date=start_dt.strftime("%Y%m%d%H%M"),
            end_date=end_dt.strftime("%Y%m%d%H%M"),
        )
        vehicles = evaluation.get("VehicleList") or evaluation.get("EvaluationVehicles")
        if vehicles:
            ev = vehicles[0]
            if ev.get("Distance") is not None:
                eval_distance = float(ev["Distance"])
            if ev.get("TotalFuelConsumption") is not None:
                eval_fuel = float(ev["TotalFuelConsumption"])
    except Exception:
        pass

    # ── 4. Resumen ───────────────────────────────────────────────────
    # ── 4. Resumen ───────────────────────────────────────────────────
    resumen: Optional[VehicleSummaryData] = None
    if len(historico) >= 2:
        inicio, fin = historico[0], historico[-1]
        km_value = eval_distance if eval_distance is not None else fin.km_recorridos - inicio.km_recorridos
        diesel_value = eval_fuel if eval_fuel is not None else (
                (fin.consumo_lts_diesel or 0) - (inicio.consumo_lts_diesel or 0)
        )
        resumen = VehicleSummaryData(
            vin=vin,
            start_timestamp=inicio.timestamp,
            end_timestamp=fin.timestamp,
            km_recorridos=km_value,
            consumo_lts_diesel=diesel_value,
            lts_adblue_consumidos=adblue_consumido,
            odometro=fin.km_recorridos,
        )
    # ------- NUEVO: Si no hay históricos, pero sí evaluación -------
    elif eval_distance is not None or eval_fuel is not None:
        # Usa los datos de los parámetros originales como timestamp
        try:
            start_dt = datetime.fromisoformat(starttime.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(stoptime.replace("Z", "+00:00"))
        except Exception:
            start_dt = None
            end_dt = None
        resumen = VehicleSummaryData(
            vin=vin,
            start_timestamp=start_dt,
            end_timestamp=end_dt,
            km_recorridos=eval_distance if eval_distance is not None else 0,
            consumo_lts_diesel=eval_fuel if eval_fuel is not None else 0,
            lts_adblue_consumidos=adblue_consumido,  # normalmente será 0
            odometro=eval_distance if eval_distance is not None else 0,
        )

    return {
        "historical_data": historico,
        "summary": resumen,
    }

