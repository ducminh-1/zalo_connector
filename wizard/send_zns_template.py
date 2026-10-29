# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
import re
import logging
from datetime import datetime

class SendZNSTemplate(models.TransientModel):
    _name = "send.zns.template"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string="Partner", default=lambda self: self._get_default_partner())
    zalo_oa_id = fields.Many2one('zalo.oa', string="Zalo OA")
    zns_rating_template_id = fields.Many2one('zns.template', string="ZNS Template")

    def _get_default_partner(self):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        if active_id and active_model:
            record = self.env[active_model].browse(active_id)
            return record.partner_id.id
        return None

    def create_zns_template(self, order_id=None, sale_order_id=None):
        if order_id:
            pos_order = self.env['pos.order'].sudo().browse(int(order_id))

            zns_template_vals = []
            key_fields = pos_order.zns_template_id.template_data

            for key_field in key_fields:
                field_value = ''
                if key_field.field_type.ttype == 'many2one':
                    related_field = getattr(pos_order, key_field.field_type.name, False)
                    if related_field:
                        field_value = related_field.name
                elif key_field.field_type.ttype in ['date', 'datetime']:
                    date_value = getattr(pos_order, key_field.field_type.name, False)
                    if date_value:
                        field_value = datetime.strftime(date_value, "%d/%m/%Y")
                    else:
                        field_value = datetime.strptime(date_value, "%Y-%m-%d").strftime("%d/%m/%Y")
                else:
                    field_value = getattr(pos_order, key_field.field_type.name, False) or ''

                zns_template_vals.append((0, 0, {'name': key_field.name, 'value': str(field_value)}))
            if zns_template_vals:
                phone_number = re.sub(r'^0', '+84', pos_order.partner_id.phone) if pos_order.partner_id.phone else ''
                template_id = pos_order.zns_template_id.zns_template_id
                body = pos_order.zns_template_id.name

                message = self.env['zns.messages'].sudo().create({
                    'number': phone_number,
                    'template_id': template_id,
                    'body': body,
                    'zns_template_val_ids': zns_template_vals
                })
        elif sale_order_id:
            sale_order = self.env['sale.order'].browse(int(sale_order_id))
            zns_template_vals = []
            key_fields = sale_order.zns_template_id.template_data

            for key_field in key_fields:
                field_value = ''
                if key_field.field_type.ttype == 'many2one':
                    related_field = getattr(sale_order, key_field.field_type.name, False)
                    if related_field:
                        field_value = related_field.name
                elif key_field.field_type.ttype in ['date', 'datetime']:
                    date_value = getattr(sale_order, key_field.field_type.name, False)
                    if date_value:
                        field_value = datetime.strftime(date_value, "%d/%m/%Y")
                    else:
                        field_value = datetime.strptime(date_value, "%Y-%m-%d").strftime("%d/%m/%Y")
                else:
                    field_value = getattr(sale_order, key_field.field_type.name, False) or ''

                zns_template_vals.append((0, 0, {'name': key_field.name, 'value': str(field_value)}))
            if zns_template_vals:
                phone_number = re.sub(r'^0', '+84', sale_order.partner_id.phone) if sale_order.partner_id.phone else ''
                template_id = sale_order.zns_template_id.zns_template_id
                body = sale_order.zns_template_id.name

                message = self.env['zns.messages'].sudo().create({
                    'number': phone_number,
                    'template_id': template_id,
                    'body': body,
                    'zns_template_val_ids': zns_template_vals
                })
        return True
