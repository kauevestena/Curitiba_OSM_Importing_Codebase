
DEFAULT_CRS = 'EPSG:31982'

# always end urls with a '/'
ROOT_URL = 'https://geocuritiba.ippuc.org.br/server/rest/services/GeoCuritiba/'

MAPSERVER_URL = 'https://geocuritiba.ippuc.org.br/server/rest/services/GeoCuritiba/Publico_Interno_GeoCuritiba_BaseCartografica_para_BC/MapServer/'

MAPSERVER_URL_ALT = 'https://geocuritiba.ippuc.org.br/server/rest/services/GeoCuritiba/Publico_Interno_GeoCuritiba_BaseCartografica_para_MC/MapServer/'


# doesn't matter they're numbers, they must be stored as strings,
# sometimes an ID like "01" occurs, thus being impossible to store as an int
LAYER_IDS = {
    'buildings': '72',
    'buildings_alt': '62'
}

