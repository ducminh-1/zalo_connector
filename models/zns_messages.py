from odoo import fields, models, api, _
import logging
import requests 
from datetime import datetime, timedelta
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class ZNSTemplateMessage(models.Model):
    _name = 'zns.messages'
    _description = 'Message'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'body'

    number = fields.Char('Number')
    body = fields.Text()
    partner_id = fields.Many2one('res.partner', 'Customer')
    state = fields.Selection([
        ('outgoing', 'In Queue'),
        ('sent', 'Sent'),
        ('error', 'Error'),
        ('canceled', 'Canceled')
    ], 'SMS Status', readonly=True, copy=False, default='outgoing', required=True)
    date_exec = fields.Datetime(string="Execute Date", default=fields.Datetime.now())
    zns_template_id = fields.Many2one('zns.template')
    template_id = fields.Char()
    zns_template_val_ids = fields.One2many('zns.template.line', 'message_id')
    campaign_id = fields.Many2one('zns.campaign', string='ZNS Campaign')

    def send_zns_template(self):
        for rec in self:
            zalo_oa = self.env['zalo.oa'].search([])
            if not zalo_oa:
                raise UserError(_("Zalo OA is not configured."))
            access_token = zalo_oa[0].access_token
            url = f'https://business.openapi.zalo.me/message/template'
            headers = {'access_token': access_token}
            key_fields = rec.zns_template_val_ids
            datas = {key_field.name: key_field.value for key_field in key_fields}
            data = {
                "phone": rec.number,
                "template_id": rec.template_id,
                "template_data": datas
            }
            try:
                response = requests.post(url, json=data, headers=headers)
                response_data = response.json()
                if response.status_code == 200:
                    if rec.number and response_data.get('message') == 'Success':
                        rec.update({'state': 'sent'})
                    else:
                        rec.update({'state': 'error'})
                        rec.message_post(body=f"API Error: {response_data.get('message')}", message_type='notification')
                else:
                    rec.message_post(body=f"API Error: {response_data.get('message')}", message_type='notification')
                    rec.update({'state': 'error'})
            except Exception as e:
                _logger.error('================Send ZNS Tempalte Error=============\n %s' % e)
                rec.update({'state': 'error'})

    def _action_send_failed_messages(self):
        failed_send_messages = self.search([('state', '=', 'error')], limit=1)
        return failed_send_messages.send_zns_template()

    def action_set_canceled(self):
        self.write({'state': 'canceled'})        

    @api.model
    def _process_send_message_queue(self, ids=None):
        filtered_ids = self.search([('state', '=', 'outgoing')], order="id asc", limit=10)
        if ids:
            ids = list(set(filtered_ids.ids) & set(ids))
        else:
            ids = filtered_ids.ids
        ids.sort()
        res = None
        try:
            res = self.browse(ids).send_zns_template()
        except Exception as e:
            _logger.error('==========Fail to send meesages outgoing==========: %s' % e)
        return res

             
    

    



