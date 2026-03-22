# Copyright 2024 Binhex - Adasat Torres de León.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import datetime
from unittest.mock import MagicMock, patch

from odoo.tests import common

PLAID_ACCOUNT_ID_1 = "Qxm5dj75QXuBe5QVPAwbIN1PgEMExnCGroLgv"
PLAID_ACCOUNT_ID_2 = "Xb7kR9m3ZWuCf6RWQBxcJO2QhFNFyoDHspMhw"

PLAID_ACCOUNTS = [
    {
        "account_id": PLAID_ACCOUNT_ID_1,
        "mask": "5362",
        "name": "Checking Account 1",
    },
    {
        "account_id": PLAID_ACCOUNT_ID_2,
        "mask": "9503",
        "name": "Checking Account 2",
    },
]

TRANSACTIONS = [
    {
        "account_id": PLAID_ACCOUNT_ID_1,
        "account_owner": None,
        "amount": 500.0,
        "authorized_date": None,
        "authorized_datetime": None,
        "category": ["Food and Drink", "Restaurants"],
        "category_id": "13005000",
        "check_number": None,
        "counterparties": [],
        "date": datetime.date(2024, 6, 20),
        "datetime": None,
        "iso_currency_code": "USD",
        "location": {
            "address": None,
            "city": None,
            "country": None,
            "lat": None,
            "lon": None,
            "postal_code": None,
            "region": None,
            "store_number": None,
        },
        "logo_url": None,
        "merchant_entity_id": None,
        "merchant_name": None,
        "name": "Tectra Inc",
        "payment_channel": "in store",
        "payment_meta": {
            "by_order_of": None,
            "payee": None,
            "payer": None,
            "payment_method": None,
            "payment_processor": None,
            "ppd_id": None,
            "reason": None,
            "reference_number": None,
        },
        "pending": False,
        "pending_transaction_id": None,
        "personal_finance_category": {
            "confidence_level": "LOW",
            "detailed": "ENTERTAINMENT_SPORTING_EVENTS_AMUSEMENT_PARKS_AND_MUSEUMS",
            "primary": "ENTERTAINMENT",
        },
        "transaction_code": None,
        "transaction_id": "Mro5zaR59jCV95J8gNedi4LjoLE76qCL6MMEe",
        "transaction_type": "place",
        "unofficial_currency_code": None,
        "website": None,
    },
    {
        "account_id": PLAID_ACCOUNT_ID_1,
        "account_owner": None,
        "amount": 30.0,
        "authorized_date": None,
        "authorized_datetime": None,
        "category": ["Food and Drink", "Restaurants"],
        "category_id": "13005000",
        "check_number": None,
        "counterparties": [],
        "date": datetime.date(2024, 5, 7),
        "datetime": None,
        "iso_currency_code": "USD",
        "location": {
            "address": None,
            "city": None,
            "country": None,
            "lat": None,
            "lon": None,
            "postal_code": None,
            "region": None,
            "store_number": None,
        },
        "logo_url": None,
        "merchant_entity_id": None,
        "merchant_name": None,
        "name": "Tectra Inc 2",
        "payment_channel": "in store",
        "payment_meta": {
            "by_order_of": None,
            "payee": None,
            "payer": None,
            "payment_method": None,
            "payment_processor": None,
            "ppd_id": None,
            "reason": None,
            "reference_number": None,
        },
        "pending": False,
        "pending_transaction_id": None,
        "personal_finance_category": {
            "confidence_level": "LOW",
            "detailed": "ENTERTAINMENT_SPORTING_EVENTS_AMUSEMENT_PARKS_AND_MUSEUMS",
            "primary": "ENTERTAINMENT",
        },
        "transaction_code": None,
        "transaction_id": "Mro5zaR59jCV95J8gNedi4LjoLE76qCL6MMEu",
        "transaction_type": "place",
        "unofficial_currency_code": None,
        "website": None,
    },
]

# Transactions from a different account under the same Plaid item
TRANSACTIONS_OTHER_ACCOUNT = [
    {
        "account_id": PLAID_ACCOUNT_ID_2,
        "account_owner": None,
        "amount": -1750.0,
        "authorized_date": None,
        "authorized_datetime": None,
        "category": None,
        "category_id": None,
        "check_number": None,
        "counterparties": [],
        "date": datetime.date(2024, 6, 5),
        "datetime": None,
        "iso_currency_code": "USD",
        "location": {
            "address": None,
            "city": None,
            "country": None,
            "lat": None,
            "lon": None,
            "postal_code": None,
            "region": None,
            "store_number": None,
        },
        "logo_url": None,
        "merchant_entity_id": None,
        "merchant_name": None,
        "name": "LEASE PAYMENT OTHER ACCT",
        "payment_channel": "other",
        "payment_meta": {
            "by_order_of": None,
            "payee": None,
            "payer": None,
            "payment_method": None,
            "payment_processor": None,
            "ppd_id": None,
            "reason": None,
            "reference_number": None,
        },
        "pending": False,
        "pending_transaction_id": None,
        "personal_finance_category": {
            "confidence_level": "LOW",
            "detailed": "INCOME_RENTAL",
            "primary": "INCOME",
        },
        "transaction_code": None,
        "transaction_id": "OtherAcct1234567890abcdefghijklmnopqrst",
        "transaction_type": "special",
        "unofficial_currency_code": None,
        "website": None,
    },
]

# Mixed: transactions from both accounts (simulates the bug scenario)
TRANSACTIONS_MIXED = TRANSACTIONS + TRANSACTIONS_OTHER_ACCOUNT

EMPTY_TRANSACTIONS = []


class TestAccountStatementImportOnlinePlaid(common.TransactionCase):
    post_install = True

    def setUp(self):
        super().setUp()

        self.now = datetime.datetime.now()
        self.currency_eur = self.env.ref("base.EUR")
        self.currency_usd = self.env.ref("base.USD")
        self.AccountJournal = self.env["account.journal"]
        self.ResPartnerBank = self.env["res.partner.bank"]
        self.OnlineBankStatementProvider = self.env["online.bank.statement.provider"]
        self.AccountBankStatement = self.env["account.bank.statement"]
        self.AccountBankStatementLine = self.env["account.bank.statement.line"]
        self.AccountStatementPull = self.env["online.bank.statement.pull.wizard"]

        self.currency_eur.write({"active": True})

        self.bank_account = self.ResPartnerBank.create(
            {
                "acc_number": "FR0214508000302245362775K46",
                "partner_id": self.env.user.company_id.partner_id.id,
            }
        )
        self.journal = self.AccountJournal.create(
            {
                "name": "Bank",
                "type": "bank",
                "code": "BANK",
                "currency_id": self.currency_eur.id,
                "bank_statements_source": "online",
                "bank_account_id": self.bank_account.id,
            }
        )
        self.provider = self.OnlineBankStatementProvider.create(
            {
                "name": "plaid Provider",
                "service": "plaid",
                "username": "username",
                "password": "password",
                "plaid_host": "sandbox",
                "plaid_access_token": "access_token",
                "journal_id": self.journal.id,
                # To get all the moves in a month at once
                "statement_creation_mode": "monthly",
            }
        )

    @patch("plaid.api.plaid_api.PlaidApi.accounts_get")
    @patch("plaid.api.plaid_api.PlaidApi.transactions_get")
    def test_import_online_bank_statement_plaid(self, trasactions_get, accounts_get):
        trasactions_get.return_value = {
            "transactions": TRANSACTIONS,
            "total_transactions": len(TRANSACTIONS),
        }
        # Plaid item accounts (our patch resolves journal.acc_number → account_id
        # via /accounts/get on the first sync).
        accounts_get.return_value = {"accounts": PLAID_ACCOUNTS}
        vals = {
            "date_since": datetime.datetime(2024, 5, 1),
            "date_until": datetime.datetime(2024, 6, 30),
        }
        wizard = (
            self.env["online.bank.statement.pull.wizard"]
            .with_context(
                active_model="account.journal",
                active_id=self.journal.id,
            )
            .create(vals)
        )
        wizard.action_pull()
        statements = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(statements), 2)
        lines = statements.line_ids
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].amount, -500.0)
        self.assertEqual(lines[1].amount, -30.0)

    @patch("plaid.api.plaid_api.PlaidApi.accounts_get")
    @patch("plaid.api.plaid_api.PlaidApi.transactions_get")
    def test_multi_account_filtering(self, transactions_get, accounts_get):
        """When a Plaid item has multiple bank accounts, only transactions
        for the account matching this provider's journal should be imported."""
        # Set the journal's bank account number to match account 1
        self.bank_account.write({"acc_number": "FR0214508000302245365362"})

        accounts_get.return_value = {"accounts": PLAID_ACCOUNTS}

        # Return only account 1 transactions when filtered
        def filter_by_account(request):
            opts = request.get("options", {})
            acct_ids = getattr(opts, "account_ids", None) if opts else None
            if acct_ids and PLAID_ACCOUNT_ID_1 in acct_ids:
                return {
                    "transactions": TRANSACTIONS,
                    "total_transactions": len(TRANSACTIONS),
                }
            return {
                "transactions": TRANSACTIONS_MIXED,
                "total_transactions": len(TRANSACTIONS_MIXED),
            }

        transactions_get.side_effect = filter_by_account

        vals = {
            "date_since": datetime.datetime(2024, 5, 1),
            "date_until": datetime.datetime(2024, 6, 30),
        }
        wizard = (
            self.env["online.bank.statement.pull.wizard"]
            .with_context(
                active_model="account.journal",
                active_id=self.journal.id,
            )
            .create(vals)
        )
        wizard.action_pull()

        # Should have resolved and cached the plaid_account_id
        self.assertEqual(self.provider.plaid_account_id, PLAID_ACCOUNT_ID_1)

        # Should only have the 2 transactions from account 1, not the
        # third transaction from account 2
        statements = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id)]
        )
        lines = statements.line_ids
        self.assertEqual(len(lines), 2)
        self.assertFalse(
            any("OTHER ACCT" in (line.payment_ref or "") for line in lines),
            "Transactions from other Plaid accounts should not be imported",
        )

    @patch("plaid.api.plaid_api.PlaidApi.accounts_get")
    @patch("plaid.api.plaid_api.PlaidApi.transactions_get")
    def test_resolve_account_id_cached(self, transactions_get, accounts_get):
        """The Plaid account ID should be resolved once and cached."""
        self.bank_account.write({"acc_number": "FR0214508000302245365362"})
        self.provider.plaid_account_id = PLAID_ACCOUNT_ID_1

        transactions_get.return_value = {
            "transactions": TRANSACTIONS,
            "total_transactions": len(TRANSACTIONS),
        }

        vals = {
            "date_since": datetime.datetime(2024, 5, 1),
            "date_until": datetime.datetime(2024, 6, 30),
        }
        wizard = (
            self.env["online.bank.statement.pull.wizard"]
            .with_context(
                active_model="account.journal",
                active_id=self.journal.id,
            )
            .create(vals)
        )
        wizard.action_pull()

        # accounts_get should NOT be called since plaid_account_id was cached
        accounts_get.assert_not_called()

    def test_get_services(self):
        services = self.provider._get_available_services()
        self.assertTrue(services)
        self.assertIn(("plaid", "Plaid.com"), services)

    @patch("plaid.api.plaid_api.PlaidApi.link_token_create")
    def test_action_sycn_with_plaid(self, link_token_create):
        link_token_create.return_value = MagicMock(
            to_dict=lambda: {"link_token": "isalinktoken", "expiration": "isadate"}
        )
        action = self.provider.action_sync_with_plaid()
        self.assertTrue(action)
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "plaid_login")
        self.assertEqual(action["params"]["token"], "isalinktoken")
