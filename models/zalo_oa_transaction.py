import json
import requests

from odoo import api, fields, models
import logging


class ZaloChatTransaction(models.Model):
    _name = "zalo.oa.transaction"
    _description = "Zalo OA Transaction"

    json_data = fields.Text()
    transaction_type = fields.Selection(
        selection=[
            ("get_access_token", "Get Access Token"),
            ("get_authorization_code", "Get Authorization Code"),
            ("refresh_access_token", "Refresh Access Token"),
            ("send_message", "Send Message "),
        ]
    )
    zalo_oa_id = fields.Many2one("zalo.oa")
    is_success = fields.Boolean()