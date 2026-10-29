from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = "pos.order"

    phone = fields.Char(related="partner_id.phone", string="Phone")
    name_store = fields.Char(related="config_id.name", string="Store Name")
    zalo_oa_id = fields.Many2one(related="company_id.zalo_oa_id", string="Zalo OA")
    zns_template_id = fields.Many2one(related="company_id.zns_rating_template_id", string="ZNS Template")