# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    zalo_user_id = fields.Char('Zalo User Id')



    