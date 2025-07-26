import unittest
import os
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from soap_client import LegacySOAPClient, LegacySystemError

class TestLegacySOAPClient(unittest.TestCase):

    def setUp(self):
        os.environ["SOAP_WSDL_URL"] = ""
        os.environ["SOAP_USERNAME"] = "test_username"
        os.environ["SOAP_PASSWORD"] = "test_password"
        os.environ["SOAP_TIMEOUT_SECONDS"] = "5"

        LegacySOAPClient._instance = None

    def tearDown(self):
        del os.environ["SOAP_WSDL_URL"]
        del os.environ["SOAP_USERNAME"]
        del os.environ["SOAP_PASSWORD"]
        del os.environ["SOAP_TIMEOUT_SECONDS"]
        LegacySOAPClient._instance = None

    @patch('soap_client.Client')
    @patch('soap_client.Transport')
    @patch('soap_client.Session')
    def test_client_initialization_success(self, MockSession, MockTransport, MockClient):
        """
        Testa se o cliente Zeep é inicializado corretamente com as configurações.
        """
        mock_session_instance = MockSession.return_value
        
        mock_zeep_client_instance = MockClient.return_value
        
        client = LegacySOAPClient()

        MockSession.assert_called_once()
        MockTransport.assert_called_once_with(session=mock_session_instance, timeout=5)
        MockClient.assert_called_once_with("http://test-wsdl.com/service?wsdl", transport=MockTransport.return_value)
        
        self.assertIsNotNone(mock_session_instance.auth)
        self.assertEqual(mock_session_instance.auth.username, "testuser")
        self.assertEqual(mock_session_instance.auth.password, "testpassword")
        
        self.assertIsInstance(client, LegacySOAPClient)
        self.assertEqual(client.client, mock_zeep_client_instance)

    @patch('soap_client.Client')
    @patch('soap_client.Transport')
    @patch('soap_client.Session')
    def test_client_initialization_failure(self, MockSession, MockTransport, MockClient):
        """
        Testa se a inicialização do cliente Zeep falha e levanta RuntimeError.
        """
        MockClient.side_effect = Exception("Erro de conexão ao WSDL") 
        
        with self.assertRaises(RuntimeError) as cm:
            LegacySOAPClient()
        self.assertIn("Não foi possível inicializar o cliente SOAP", str(cm.exception))

    @patch('soap_client.LegacySOAPClient.client')
    def test_get_user_data_success(self, mock_zeep_client_service):
        """
        Testa a chamada bem-sucedida da operação get_user_data.
        """
        mock_zeep_client_service.service.GetUser.return_value = {"id": "user123", "name": "Test User"}
        
        client = LegacySOAPClient()
        user_data = client.get_user_data("user123")

        mock_zeep_client_service.service.GetUser.assert_called_once_with(userId="user123")
        self.assertEqual(user_data, {"id": "user123", "name": "Test User"})

    @patch('soap_client.LegacySOAPClient.client')
    def test_get_user_data_fault(self, mock_zeep_client_service):
        """
        Testa o tratamento de um SOAP Fault na operação get_user_data.
        """
        from zeep.exceptions import Fault
        mock_zeep_client_service.service.GetUser.side_effect = Fault(message="Usuário não encontrado", code="123")
        
        client = LegacySOAPClient()
        with self.assertRaises(LegacySystemError) as cm:
            client.get_user_data("nonexistent_user")
        self.assertIn("Erro do sistema legado: Usuário não encontrado", str(cm.exception))

    @patch('soap_client.LegacySOAPClient.client')
    def test_update_product_stock_success(self, mock_zeep_client_service):
        """
        Testa a chamada bem-sucedida da operação update_product_stock.
        """
        mock_zeep_client_service.service.UpdateProductStock.return_value = True
        
        client = LegacySOAPClient()
        success = client.update_product_stock("prod456", 100)

        mock_zeep_client_service.service.UpdateProductStock.assert_called_once_with(productId="prod456", newQuantity=100)
        self.assertTrue(success)

    @patch('soap_client.LegacySOAPClient.client')
    def test_update_product_stock_connection_error(self, mock_zeep_client_service):
        """
        Testa o tratamento de um ConnectionError na operação update_product_stock.
        """
        mock_zeep_client_service.service.UpdateProductStock.side_effect = ConnectionError("Serviço indisponível")
        
        client = LegacySOAPClient()
        with self.assertRaises(LegacySystemError) as cm:
            client.update_product_stock("prod456", 100)
        self.assertIn("Erro de conexão com o serviço legado: Serviço indisponível", str(cm.exception))

    @patch('soap_client.LegacySOAPClient.client')
    def test_singleton_behavior(self, mock_zeep_client_service):
        """
        Testa se a classe LegacySOAPClient se comporta como um singleton.
        """
        client1 = LegacySOAPClient()
        client2 = LegacySOAPClient()
        
        self.assertIs(client1, client2)
        mock_zeep_client_service.reset_mock()
        LegacySOAPClient._instance = None
        LegacySOAPClient()
        LegacySOAPClient()
        mock_zeep_client_service.assert_called_once()

if __name__ == '__main__':
    unittest.main()