from urllib.parse import urlencode

from models.estadio_coordenadas import ESTADIOS
from services.texto_util import normalizar_texto

def gerar_link_rota_google_maps(time, endereco_origem, modo='driving'):
    """Monta a rota do Google Maps usando o endereço salvo no perfil."""
    time_norm = normalizar_texto(time)
    chave_encontrada = None
    for chave in ESTADIOS.keys():
        if normalizar_texto(chave) in time_norm or time_norm in normalizar_texto(chave):
            chave_encontrada = chave
            break

    if not chave_encontrada:
        raise ValueError(f"Time '{time}' não reconhecido para cálculo de rota.")
    if not endereco_origem or not endereco_origem.strip():
        raise ValueError('Cadastre seu endereço no perfil antes de calcular a rota.')
    if modo not in ('driving', 'transit'):
        raise ValueError('Escolha carro ou ônibus/metrô para calcular a rota.')

    estadio = ESTADIOS[chave_encontrada]
    parametros = urlencode({
        'api': '1',
        'origin': endereco_origem.strip(),
        'destination': estadio['nome'],
        'travelmode': modo,
    })
    return {
        'origem': endereco_origem.strip(),
        'estadio_nome': estadio['nome'],
        'modo': modo,
        'link': f'https://www.google.com/maps/dir/?{parametros}',
    }
