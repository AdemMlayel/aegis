
import pycurl
def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         return True
class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, pool_size, use_pool=True):
        pool_size = int(pool_size)
        use_pool = str_to_bool(use_pool)
        self.pool_size = pool_size
        HOSTNAME_PLACEHOLDER = []
        # Crear una sesión compartida para TLS/DNS
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER(pycurl.SH_SHARE, pycurl.LOCK_DATA_DNS)
        HOSTNAME_PLACEHOLDER(pycurl.SH_SHARE, pycurl.LOCK_DATA_SSL_SESSION)
        
        # Crear un pool de conexiones curl
        if use_pool:
            for _ in range(pool_size):
                curl = HOSTNAME_PLACEHOLDER()
                HOSTNAME_PLACEHOLDER(pycurl.FORBID_REUSE, 0)  # Permitir reutilización de conexiones
                HOSTNAME_PLACEHOLDER(pycurl.FRESH_CONNECT, 0)  # Evitar abrir una nueva conexión cada vez
                HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER)  # Asociar la sesión compartida
                HOSTNAME_PLACEHOLDER(curl)
        else:
            curl = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(pycurl.FORBID_REUSE, 1)  # Forzar cierre de conexión tras uso
            HOSTNAME_PLACEHOLDER(pycurl.FRESH_CONNECT, 1)  # Forzar nueva conexión
            HOSTNAME_PLACEHOLDER(pycurl.DNS_CACHE_TIMEOUT, 0)  # Deshabilitar caché de DNS completamente
            HOSTNAME_PLACEHOLDER(curl)

    def get_curl_connection(self):
        # Recuperar una conexión del pool
        if HOSTNAME_PLACEHOLDER:
            return HOSTNAME_PLACEHOLDER(0)
        else:
            return HOSTNAME_PLACEHOLDER()  # Si el pool está vacío, crear una nueva conexión

    def release_connection(self, curl):
        # Devolver la conexión al pool
        HOSTNAME_PLACEHOLDER(curl)

    def close_all_connections(self):
        # Cerrar todas las conexiones en el pool
        for curl in HOSTNAME_PLACEHOLDER:
            HOSTNAME_PLACEHOLDER()