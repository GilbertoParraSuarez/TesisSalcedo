from datetime import datetime
from actions.api.models.models import LecturaOut

def create_lectura_out(payload, lectura_id="syncid123"):
    return LecturaOut(
        id=lectura_id,
        planta_id=payload["planta_id"],
        humedad=payload["humedad"],
        temperatura=payload["temperatura"],
        ec=payload["ec"],
        ph=payload["ph"],
        nitrogeno=payload["nitrogeno"],
        fosforo=payload["fosforo"],
        potasio=payload["potasio"],
        fecha=datetime.fromisoformat(payload["fecha"].replace("Z", "+00:00")),
        notas=payload["notas"]
    )