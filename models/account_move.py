from odoo import models, fields, api
import logging
import json
import requests 
import re

class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_zns_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create ZNS Template',
            'res_model': 'send.zns.template',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'active_id': self.id,
                'active_model': 'account.move',
            }
        }