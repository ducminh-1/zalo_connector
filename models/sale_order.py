from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json
import requests 
import datetime
import re
_logger = logging.getLogger("")

class SaleOrder(models.Model):
    _inherit = 'sale.order'
        
    zalo_oa_id = fields.Many2one('zalo.oa', string="Zalo OA")
    zns_template_id = fields.Many2one('zns.template', string="ZNS Template")
    partner_id = fields.Many2one('res.partner', string="Partner")
    phone = fields.Char(related="partner_id.phone", string="Phone")   

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
                'active_model': 'sale.order',
            }
        }

