# Copyright 2024 Binhex - Adasat Torres de León.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError

AVAILABLE_LANGS = [
    "da",
    "nl",
    "en",
    "et",
    "fr",
    "de",
    "hi",
    "it",
    "lv",
    "lt",
    "no",
    "pl",
    "pt",
    "ro",
    "es",
    "sv",
    "vi",
]


class OnlineBankStatementProvider(models.Model):
    _inherit = "online.bank.statement.provider"
    plaid_access_token = fields.Char()
    plaid_account_id = fields.Char(
        help="Plaid account ID used to filter transactions to this specific "
        "bank account. Resolved automatically from the journal's bank "
        "account number on first sync.",
    )
    plaid_host = fields.Selection(
        [
            ("sandbox", "Sandbox"),
            ("production", "Production"),
        ],
        default="sandbox",
    )

    def _obtain_statement_data(self, date_since, date_until):
        self.ensure_one()
        if self.service != "plaid":
            return super()._obtain_statement_data(date_since, date_until)
        return self._plaid_retrieve_data(date_since, date_until), {}

    @api.model
    def _get_available_services(self):
        return super()._get_available_services() + [
            ("plaid", "Plaid.com"),
        ]

    def _country_code(self):
        if self.journal_id.bank_id and self.journal_id.bank_id.country:
            return self.journal_id.bank_id.country.code
        if self.journal_id.company_id.country_id:
            return self.journal_id.company_id.country_id.code
        raise UserError(
            self.env._("Country code not found for the bank or the company...")
        )

    def _verify_lang(self, lang):
        if lang not in AVAILABLE_LANGS:
            return "en"
        return lang

    def action_sync_with_plaid(self):
        self.ensure_one()
        plaid_interface = self.env["plaid.interface"]
        args = [self.username, self.password, self.plaid_host]
        client = plaid_interface._client(*args)
        lang = (
            self.env["res.lang"]._lang_get(self.env.lang or self.env.user.lang).iso_code
        )
        company_name = self.env.company.name

        link_token = plaid_interface._link(
            client=client,
            language=self._verify_lang(lang),
            country_code=self._country_code(),
            company_name=company_name,
            products=["transactions"],
        )
        return {
            "type": "ir.actions.client",
            "tag": "plaid_login",
            "params": {
                "call_model": "online.bank.statement.provider",
                "call_method": "plaid_create_access_token",
                "token": link_token,
                "object_id": self.id,
            },
            "target": "new",
        }

    def _plaid_resolve_account_id(self, client):
        """Resolve the journal's bank account number to a Plaid account ID.

        When a Plaid item contains multiple bank accounts, we must filter
        transactions to only the account that matches this provider's journal.
        """
        account_number = self.account_number
        if not account_number:
            # No journal bank account number to match against — leave
            # filtering off, same as the unmodified upstream behavior.
            return False
        plaid_interface = self.env["plaid.interface"]
        accounts = plaid_interface._get_accounts(client, self.plaid_access_token)
        # Strip leading zeros for flexible matching (some banks zero-pad)
        stripped = account_number.lstrip("0")
        for account in accounts:
            mask = account.get("mask", "")
            acct_id = account.get("account_id", "")
            # Plaid mask is typically the last 4 digits
            if mask and (account_number.endswith(mask) or stripped.endswith(mask)):
                return acct_id
        return False

    def _plaid_retrieve_data(self, date_since, date_until):
        if not self.plaid_access_token:
            raise UserError(
                self.env._(
                    "Please link your Plaid account first by "
                    "clicking on 'Sync with Plaid'."
                )
            )
        plaid_interface = self.env["plaid.interface"]
        args = [self.username, self.password, self.plaid_host]
        client = plaid_interface._client(*args)
        # Resolve and cache the Plaid account ID for filtering
        if not self.plaid_account_id:
            resolved = self._plaid_resolve_account_id(client)
            if resolved:
                self.plaid_account_id = resolved
        account_ids = [self.plaid_account_id] if self.plaid_account_id else None
        transactions = plaid_interface._get_transactions(
            client, self.plaid_access_token, date_since, date_until, account_ids
        )
        return self._prepare_vals_for_statement(transactions)

    @api.model
    def plaid_create_access_token(self, public_token, active_id):
        provider = self.browse(active_id)
        plaid_interface = self.env["plaid.interface"]
        client = plaid_interface._client(
            provider.username, provider.password, provider.plaid_host
        )
        args = [client, public_token]
        provider.plaid_access_token = plaid_interface._login(*args)
        if provider.plaid_access_token:
            return True
        return False

    def _prepare_vals_for_statement(self, transactions):
        return [
            {
                "date": transaction["date"],
                "ref": transaction["name"],
                "payment_ref": transaction["name"],
                "unique_import_id": transaction["transaction_id"],
                "amount": float(transaction["amount"]) * -1.00,
                "raw_data": transaction,
            }
            for transaction in transactions
        ]
