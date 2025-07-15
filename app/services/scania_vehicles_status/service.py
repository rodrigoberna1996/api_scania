# app/services/scania_vehicles_status/service.py
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.scania_vehicles_status.client import vehicle_status_client
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
                lts_adblue_consumidos=adblue_raw,  # valor tal cual
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

    # ── 4. Resumen ───────────────────────────────────────────────────
    resumen: Optional[VehicleSummaryData] = None
    if len(historico) >= 2:
        inicio, fin = historico[0], historico[-1]
        resumen = VehicleSummaryData(
            vin=vin,
            start_timestamp=inicio.timestamp,
            end_timestamp=fin.timestamp,
            km_recorridos=fin.km_recorridos - inicio.km_recorridos,
            consumo_lts_diesel=(fin.consumo_lts_diesel or 0)
            - (inicio.consumo_lts_diesel or 0),
            lts_adblue_consumidos=adblue_consumido,
        )

    return {
        "historical_data": historico,
        "summary": resumen,
    }
