__author__ = 'frank'

# Setup our test environment
import os
os.environ['NETKI_ENV'] = 'test'

from unittest import TestCase

from netki.api.domain import *

from mock import patch, Mock


class TestWalletLookup(TestCase):
    # This is the open wallet name lookup API

    def setUp(self):
        self.patcher1 = patch("netki.api.domain.InputValidation")
        self.patcher2 = patch("netki.api.domain.create_json_response")
        self.patcher3 = patch("netki.api.domain.WalletNameResolver")

        self.mockInputValidation = self.patcher1.start()
        self.mockCreateJSONResponse = self.patcher2.start()
        self.mockWalletNameResolver = self.patcher3.start()

        config.namecoin.enabled = True

    def tearDown(self):

        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()

    def get_json_call(self):
        # Utility function to get JSON call_args_list cleaning up assertions in below tests
        return self.mockCreateJSONResponse.call_args_list[0][1].get('data')

    def test_invalid_wallet_name_field(self):
        # Used to simulate failure in validation for each iteration [iteration 1, iteration 2, etc.]
        self.mockInputValidation.is_valid_field.side_effect = [False]

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 1)
        self.assertFalse(self.mockWalletNameResolver.called)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertFalse(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), 'Invalid Parameters')

    def test_invalid_currency_field(self):
        # Used to simulate failure in validation for each iteration [iteration 1, iteration 2, etc.]
        self.mockInputValidation.is_valid_field.side_effect = [True, False]

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertFalse(self.mockWalletNameResolver.called)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertFalse(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), 'Invalid Parameters')

    def test_invalid_wallet_name_field_no_dot(self):

        api_wallet_lookup('walletfrankcontrerasme', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertFalse(self.mockWalletNameResolver.called)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertFalse(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), 'Invalid Parameters')

    def test_wallet_address_returned_success(self):

        self.mockWalletNameResolver.return_value.resolve_wallet_name.return_value = '1djskfaklasdjflkasdf'

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertEqual(self.mockWalletNameResolver.return_value.resolve_wallet_name.call_count, 1)
        self.assertEqual(self.mockWalletNameResolver.return_value.set_namecoin_options.call_count, 1)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertTrue(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), '')

        # Returned Data Validation
        call_dict = self.get_json_call()
        self.assertEqual(call_dict.get('wallet_name'), 'wallet.frankcontreras.me')
        self.assertEqual(call_dict.get('currency'), 'btc')
        self.assertEqual(call_dict.get('wallet_address'), '1djskfaklasdjflkasdf')

    def test_namecoin_config_disabled(self):

        self.mockWalletNameResolver.return_value.resolve_wallet_name.return_value = '1djskfaklasdjflkasdf'
        config.namecoin.enabled = False

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertEqual(self.mockWalletNameResolver.return_value.resolve_wallet_name.call_count, 1)
        self.assertEqual(self.mockWalletNameResolver.return_value.set_namecoin_options.call_count, 0)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertTrue(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), '')

        # Returned Data Validation
        call_dict = self.get_json_call()
        self.assertEqual(call_dict.get('wallet_name'), 'wallet.frankcontreras.me')
        self.assertEqual(call_dict.get('currency'), 'btc')
        self.assertEqual(call_dict.get('wallet_address'), '1djskfaklasdjflkasdf')

    def test_wallet_lookup_returned_insecure_error(self):
        self.mockInputValidation.is_valid_field.return_value = True
        self.mockWalletNameResolver.return_value.resolve_wallet_name.side_effect = WalletNameLookupInsecureError()

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertEqual(self.mockWalletNameResolver.return_value.resolve_wallet_name.call_count, 1)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertFalse(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), 'Wallet Name Lookup is Insecure')
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('data'), {})

    def test_wallet_lookup_returned_does_not_exist(self):
        self.mockInputValidation.is_valid_field.return_value = True
        self.mockWalletNameResolver.return_value.resolve_wallet_name.side_effect = WalletNameLookupError()

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertEqual(self.mockWalletNameResolver.return_value.resolve_wallet_name.call_count, 1)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertFalse(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), 'Wallet Name does not exist')
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('data'), {})

    def test_wallet_lookup_returned_empty_currency_list(self):
        self.mockInputValidation.is_valid_field.return_value = True
        self.mockWalletNameResolver.return_value.resolve_wallet_name.side_effect = WalletNameUnavailableError()

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertEqual(self.mockWalletNameResolver.return_value.resolve_wallet_name.call_count, 1)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertFalse(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), 'Wallet Name does not exist')
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('data'), {})

    def test_wallet_lookup_returned_currency_unavailable(self):
        self.mockInputValidation.is_valid_field.return_value = True
        self.mockWalletNameResolver.return_value.resolve_wallet_name.side_effect = WalletNameCurrencyUnavailableError()

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertEqual(self.mockWalletNameResolver.return_value.resolve_wallet_name.call_count, 1)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertFalse(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), 'Wallet Name Does Not Contain Requested Currency')
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('data'), {})

    def test_wallet_lookup_exception(self):

        self.mockWalletNameResolver.return_value.resolve_wallet_name.side_effect = Exception('Raising Exception for testing')

        api_wallet_lookup('wallet.frankcontreras.me', 'btc')

        self.assertEqual(self.mockInputValidation.is_valid_field.call_count, 2)
        self.assertEqual(self.mockWalletNameResolver.return_value.resolve_wallet_name.call_count, 1)
        self.assertEqual(self.mockCreateJSONResponse.call_count, 1)
        self.assertFalse(self.mockCreateJSONResponse.call_args_list[0][1].get('success'))
        self.assertEqual(self.mockCreateJSONResponse.call_args_list[0][1].get('message'), 'General Wallet Lookup Failure')

    def test_uppercase_currency_and_wallet_name_to_lowercase(self):

        api_wallet_lookup('Wallet.FrankContreras.Me', 'BTC')

        # Validate call to resolve has values in lowercase
        call_args = self.mockWalletNameResolver.return_value.resolve_wallet_name.call_args_list[0][0]
        self.assertEqual('wallet.frankcontreras.me', call_args[0])
        self.assertEqual('btc', call_args[1])

    def test_dogecoin_transform(self):

        api_wallet_lookup('wallet.frankContreras.me', 'doge')

        # Validate call to resolve has values in lowercase
        call_args = self.mockWalletNameResolver.return_value.resolve_wallet_name.call_args_list[0][0]
        self.assertEqual('wallet.frankcontreras.me', call_args[0])
        self.assertEqual('dgc', call_args[1])

if __name__ == "__main__":
    import unittest
    unittest.main()