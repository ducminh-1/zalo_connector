# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'
    _check_company_auto = True

    zalo_oa_id = fields.Many2one(
        "zalo.oa", string="Zalo OA",
        domain="['|', ('company_id', '=', False), ('company_id', '=', id)]",
        check_company=True,)
    zns_rating_template_id = fields.Many2one(
        "zns.template", string="Default Template",
        domain="['|', ('company_id', '=', False), ('company_id', '=', id)]",
        check_company=True,
    )