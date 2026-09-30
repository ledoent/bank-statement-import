# Copyright 2024 Binhex - Adasat Torres de León.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Online Bank Statements: plaid.com",
    "version": "20.0.1.0.0",
    "category": "Account",
    "website": "https://github.com/OCA/bank-statement-import",
    "author": "Binhex, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["account_statement_import_online"],
    "data": [
        "views/online_bank_statement_provider.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # The vendored Plaid Link SDK is listed explicitly and lives under
            # static/lib, which is the core convention for third-party code and
            # keeps eslint/prettier off it.
            "/account_statement_import_online_plaid/static/lib/link/v2/stable/link-initialize.js",
            "/account_statement_import_online_plaid/static/src/js/plaid_integration.esm.js",
        ],
    },
    "external_dependencies": {
        "python": ["plaid-python"],
    },
}
