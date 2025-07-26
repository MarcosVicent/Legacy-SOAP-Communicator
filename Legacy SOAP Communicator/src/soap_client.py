import os
import logging
from functools import wraps
from zeep import Client, Transport
from zeep.exceptions import Fault, XMLSyntaxError
from requests import Session
from requests.auth import HTTPBasicAuth

SOAP_WSDL_URL = os.getenv("SOAP_WSDL_URL", "")
SOAP_USERNAME = os.getenv("SOAP_USERNAME")
SOAP_PASSWORD = os.getenv("SOAP_PASSWORD")
SOAP_TIMEOUT_SECONDS = int(os.getenv("SOAP_TIMEOUT_SECONDS", "30"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def soap_error_handler(func):
    """
    Um decorador para envolver chamadas SOAP com tratamento de erro comum.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Fault as e:
            logger.error(f"Ocorreu um SOAP Fault em {func.__name__}: {e.message}", exc_info=True)
            raise LegacySystemError(f"Erro do sistema legado: {e.message}") from e
        except XMLSyntaxError as e:
            logger.error(f"Erro de Sintaxe XML durante a comunicação SOAP em {func.__name__}: {e}", exc_info=True)
            raise LegacySystemError(f"Erro de sintaxe XML: {e}") from e
        except ConnectionError as e:
            logger.error(f"Erro de Conexão com o serviço SOAP em {func.__name__}: {e}", exc_info=True)
            raise LegacySystemError(f"Erro de conexão com o serviço legado: {e}") from e
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado em {func.__name__}: {e}", exc_info=True)
            raise LegacySystemError(f"Erro inesperado ao comunicar com sistema legado: {e}") from e
    return wrapper

class LegacySystemError(Exception):
    """Exceção personalizada para erros originados do sistema legado."""
    pass

class LegacySOAPClient:
    """
    Lida com a comunicação com um serviço SOAP legado.
    Segue o padrão Singleton (ou efetivamente, um cliente de nível de módulo) para evitar a reinicialização
    do cliente Zeep a cada chamada, o que pode ser caro.
    """
    _instance = None

    def __new__(cls, wsdl_url: str = SOAP_WSDL_URL, username: str = SOAP_USERNAME, password: str = SOAP_PASSWORD, timeout: int = SOAP_TIMEOUT_SECONDS):
        if cls._instance is None:
            cls._instance = super(LegacySOAPClient, cls).__new__(cls)
            cls._instance._initialize_client(wsdl_url, username, password, timeout)
        return cls._instance

    def _initialize_client(self, wsdl_url: str, username: str, password: str, timeout: int):
        logger.info(f"Inicializando cliente Zeep SOAP para WSDL: {wsdl_url}")
        session = Session()
        if username and password:
            session.auth = HTTPBasicAuth(username, password)
            logger.info("Autenticação básica configurada para o cliente SOAP.")
        
        transport = Transport(session=session, timeout=timeout)
        try:
            self.client = Client(wsdl_url, transport=transport)
            logger.info("Cliente Zeep SOAP inicializado com sucesso.")
       
        except Exception as e:
            logger.critical(f"Falha ao inicializar o cliente Zeep SOAP: {e}", exc_info=True)
            raise RuntimeError(f"Não foi possível inicializar o cliente SOAP: {e}") from e

    @soap_error_handler
    def get_user_data(self, user_id: str) -> dict:
        """
        Método de exemplo para chamar uma operação 'GetUser' no sistema legado.
        Substitua 'YourService' e 'GetUser' pelos nomes reais de serviço/operação
        do seu WSDL.
        """
        try:
            response = self.client.service.GetUser(userId=user_id)
            logger.info(f"Dados do usuário recuperados com sucesso para o ID: {user_id}")
            return response
        except AttributeError as e:
            logger.error(f"Operação SOAP 'GetUser' ou serviço 'YourService' não encontrado. Verifique o WSDL e a estrutura client.service: {e}", exc_info=True)
            raise LegacySystemError(f"Operação SOAP não encontrada: {e}") from e

    @soap_error_handler
    def update_product_stock(self, product_id: str, quantity: int) -> bool:
        """
        Método de exemplo para chamar uma operação 'UpdateProductStock'.
        """
        try:
            response = self.client.service.UpdateProductStock(productId=product_id, newQuantity=quantity)
            logger.info(f"Estoque do produto ID: {product_id} atualizado com sucesso para a quantidade: {quantity}")
            return True
        except AttributeError as e:
            logger.error(f"Operação SOAP 'UpdateProductStock' ou serviço associado não encontrado: {e}", exc_info=True)
            raise LegacySystemError(f"Operação SOAP não encontrada: {e}") from e

if __name__ == "__main__":
    os.environ["SOAP_WSDL_URL"] = ""
   
    try:
        soap_client = LegacySOAPClient()
        
        print("\n--- Testando Serviço da Calculadora (operação Add) ---")
        try:
            result_add = soap_client.client.service.Add(intA=10, intB=5)
            print(f"10 + 5 = {result_add}")
        except LegacySystemError as e:
            print(f"Erro ao chamar Calculator.Add: {e}")
        except AttributeError as e:
            print(f"Erro: Operação 'Add' não encontrada no serviço Calculator. Verifique o WSDL. {e}")
        except Exception as e:
            print(f"Ocorreu um erro inesperado durante Calculator.Add: {e}")

        print("\n--- Testando Serviço da Calculadora (operação Divide) ---")
        try:
            result_divide = soap_client.client.service.Divide(intA=10, intB=2)
            print(f"10 / 2 = {result_divide}")
            
        except LegacySystemError as e:
            print(f"Erro ao chamar Calculator.Divide: {e}")
        except AttributeError as e:
            print(f"Erro: Operação 'Divide' não encontrada no serviço Calculator. Verifique o WSDL. {e}")
        except Exception as e:
            print(f"Ocorreu um erro inesperado durante Calculator.Divide: {e}")

    except RuntimeError as e:
        print(f"Erro de inicialização: {e}")
    except Exception as e:
        print(f"Ocorreu um erro não tratado: {e}")