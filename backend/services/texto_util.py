import unicodedata


def normalizar_texto(texto):
    """Tira acentos, espaços e maiúsculas: 'Atlético MG' -> 'atleticomg'.

    Usamos isso para comparar nomes sem ser enganado por acento
    (o bug antigo: "Atletico" in "Atlético MG" dava False).
    """
    if not texto:
        return ""
    # NFKD separa a letra do acento: 'é' vira 'e' + '´'
    decomposto = unicodedata.normalize('NFKD', texto)
    # descarta só os caracteres de acento (combining)
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return sem_acento.lower().replace(" ", "")
