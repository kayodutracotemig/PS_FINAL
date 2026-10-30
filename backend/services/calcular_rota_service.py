import requests
from models.estadio_coordenadas import ESTADIOS
from services.texto_util import normalizar_texto

def calcular_rota_estadio(time, user_lat, user_lon, modo='driving'):
    """
    Calcula a distância e tempo usando a API gratuita do OSRM (Open Source Routing Machine).
    """
    # Normaliza o nome do time vindo do banco (ex: "Atlético MG" -> "atleticomg")
    time_norm = normalizar_texto(time)

    # Procura a chave correspondente no dicionário de estádios
    chave_encontrada = None
    for chave in ESTADIOS.keys():
        if normalizar_texto(chave) in time_norm or time_norm in normalizar_texto(chave):
            chave_encontrada = chave
            break

    if not chave_encontrada:
        raise ValueError(f"Time '{time}' não reconhecido para cálculo de rota. Verifique o arquivo estadio_coordenadas.py")

    estadio = ESTADIOS[chave_encontrada]
    dest_lat = estadio['lat']
    dest_lon = estadio['lon']

    # O OSRM público só tem rotas de carro e o nome do perfil na URL é 'driving'
    # (antes era 'car'). Ônibus/metrô e Uber usam a rota de carro como estimativa.
    profile = 'driving'

    url = f"https://router.project-osrm.org/route/v1/{profile}/{user_lon},{user_lat};{dest_lon},{dest_lat}?overview=false"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 'Ok':
            raise Exception("Não foi possível calcular a rota para este local.")

        rota = data['routes'][0]
        distancia_m = rota['distance']
        duracao_s = rota['duration']

        return {
            "distancia_km": round(distancia_m / 1000, 2),
            "duracao_min": round(duracao_s / 60),
            "estadio_nome": estadio['nome'],
            "endereco": estadio.get('endereco', estadio['nome']),
            "dest_lat": dest_lat,
            "dest_lon": dest_lon
        }
    except Exception as e:
        print(f"Erro OSRM: {e}")
        raise Exception("Erro ao conectar com o serviço de mapas gratuito.")
