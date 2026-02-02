
from pathlib import Path
import geoip2.database
from fastapi import Request
from user_agents import parse
import json
import hashlib

class SessionContext:
    def __init__(self, ip: str, user_agent: dict, device_id: str, location: str | None = None):
        self.ip = ip
        self.user_agent = user_agent
        self.device_id = device_id
        self.location = location

BASE_DIR = Path(__file__).resolve().parent
MMDB_PATH = BASE_DIR / "GeoLite2-City" / "GeoLite2-City.mmdb"

try:
    geoip_reader = geoip2.database.Reader(str(MMDB_PATH))
except Exception as e:
    print("⚠ Error cargando GeoLite2:", e)
    geoip_reader = None


def get_ip_location(ip: str) -> dict:
    try:
        response = geoip_reader.city(ip)
        return f"{response.city.name}, {response.country.name} Latitud: {response.location.latitude}, Longitud: {response.location.longitude}"

    except Exception:
        # No location found or private/local IP
        return "Es una IP privada / no se pudo obtener la IP"


# Obtenemos la IP real del header
def get_ip(request: Request) -> dict:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    # Si viene una lista de IPs, toma la primera (cliente real)
    if x_forwarded_for:
        raw_ip = x_forwarded_for.split(",")[0].strip()
        IP_real = raw_ip.split(":")[0]
    else: 
        IP_real = request.client.host
    ua = parse(request.headers.get("user-agent"))
    user_agent = {
        "browser": ua.browser.family + " " + ua.browser.version_string,
        "os": ua.os.family + " " + ua.os.version_string,
        "device": (
            "Mobile" if ua.is_mobile else
            "Tablet" if ua.is_tablet else
            "Desktop"
        )
    }
    return {
        "ip": IP_real,
        "user_agent": user_agent,
        "location": get_ip_location(IP_real)
    }
    

def get_session_context(request: Request):
    """Extrae la información de la sesión del cliente desde el request."""
    ip_data = get_ip(request)
    ip = ip_data.get("ip")
    user_agent = ip_data.get("user_agent")

    device_id = create_id_device(request)

    return SessionContext(
        ip=ip,
        user_agent=user_agent,
        device_id=device_id,
        location=get_ip_location(ip)

    )

def create_id_device(request: Request) -> str:
    # Obtener datos de la sesion 
    ip_data = get_ip(request)
    user_agent = ip_data["user_agent"]
    # Crear un identificador de la session del dispositivo 
    raw = json.dumps(user_agent, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()