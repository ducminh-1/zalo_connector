# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import expression
import random
from ast import literal_eval
import ast
import logging
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
import re
# from odoo import Command
_logger = logging.getLogger(__name__)

class ZnsCampaign(models.Model):
    _name = "zns.campaign"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ZNS Campaign'
    _rec_name = 'subject'

    state = fields.Selection(
        [('draft', 'Draft'), ('in_queue', 'In Queue'),
         ('sending', 'Sending'), ('done', 'Sent')],
        string='Status',
        default='draft', required=True,
        copy=False, tracking=True)
    subject = fields.Char(
        'Subject', required=True, translate=False)
    model_id = fields.Many2one(
        'ir.model', string='Recipients Model',
        ondelete='cascade', required=True,
        domain="[('model', 'in', ['sale.order', 'res.partner', 'account.move', 'helpdesk.ticket'])]")
    model_name = fields.Char(
        string='Recipients Model Name',
        related='model_id.model', readonly=True, related_sudo=True)
    reply_to_mode = fields.Selection(
        [('update', 'Recipient Followers'), ('new', 'Specified Email Address')],
        string='Reply-To Mode',
        compute='_compute_reply_to_mode', readonly=False, store=True,
        help='Thread: replies go to target document. Email: replies are routed to a given email.')
    domain = fields.Char(
        string='Domain',
        compute='_compute_domain', readonly=False, store=True)
    notfication_type = fields.Selection([('mail', 'Email')], string="Type", default="mail", required=True)  
    model_real = fields.Char(
        string='Recipients Real Model', compute='_compute_model_real')
    zns_template = fields.Many2one('zns.template', domain="[('model_id', '=', model_id)]")
    schedule_type = fields.Selection(
        [('now', 'Send now'), ('scheduled', 'Send on')],
        string='Schedule', default='now',
        readonly=True, required=True,
        states={'draft': [('readonly', False)], 'in_queue': [('readonly', False)]})
    sent_date = fields.Datetime(string='Sent Date', copy=False)
    schedule_date = fields.Datetime(
        string='Scheduled for',
        compute='_compute_schedule_date', readonly=True, store=True,
        copy=True, tracking=True,
        states={'draft': [('readonly', False)], 'in_queue': [('readonly', False)]})
    calendar_date = fields.Datetime(
        'Calendar Date',
        compute='_compute_calendar_date', store=True,
        copy=False,
        help="Date at which the mailing was or will be sent.")
    user_id = fields.Many2one(
        'res.users', string='Responsible',
        tracking=True,
        default=lambda self: self.env.uid)
    sent = fields.Integer(compute="_compute_statistics")
    failed = fields.Integer(compute="_compute_statistics")


    def _compute_statistics(self):
        """ Compute statistics of the ZNS campaign """
        default_vals = {
            'sent': 0,
            'failed': 0,
        }
        if not self.ids:
            self.update(default_vals)
            return
        self.env.cr.execute("""
            SELECT
                c.id as campaign_id,
                COUNT(s.state) FILTER (WHERE s.state = 'sent') AS sent,
                COUNT(s.state) FILTER (WHERE s.state = 'error') AS failed
            FROM 
                zns_messages s
            RIGHT JOIN
                zns_campaign c
                ON (c.id = s.campaign_id)
            WHERE
                c.id IN %s
            GROUP BY
                c.id
        """, (tuple(self.ids), ))
        for row in self.env.cr.dictfetchall():
            self.browse(row.pop('campaign_id')).update(row)

    
    @api.depends('state', 'schedule_date')
    def _compute_calendar_date(self):
        for campaign in self:
            if campaign.state == 'done':
                campaign.calendar_date = fields.Datetime.now()
            else:
                campaign.calendar_date = False

    @api.depends('schedule_type')
    def _compute_schedule_date(self):
        for campaign in self:
            if  campaign.schedule_type == 'now' or not campaign.schedule_date:
                campaign.schedule_date = False

    @api.depends('model_id')
    def _compute_model_real(self):
        for campaign in self:
            campaign.model_real = 'mailing.contact' if campaign.model_id.model == 'mailing.list' else campaign.model_id.model

    @api.depends('model_id')
    def _compute_reply_to_mode(self):
        for campaign in self:
            if campaign.model_id.model in ['res.partner', 'sale.order', 'account.move']:
                campaign.reply_to_mode = 'new'
            else:
                campaign.reply_to_mode = 'update'

    @api.depends('model_id', 'notfication_type')
    def _compute_domain(self):
        for campaign in self:
            if not campaign.model_id:
                campaign.domain = ''
            else:
                campaign.domain = repr(campaign._get_default_domain())
  
    def _get_default_domain(self):
        domain = []
        if hasattr(self.env[self.model_name], '_get_default_domain'):
            domain = self.env[self.model_name]._get_default_domain(self)
        if self.notfication_type == 'mail' and 'is_blacklisted' in self.env[self.model_name]._fields:
            domain = expression.AND([[('is_blacklisted', '=', False)], domain])
        return domain
    
    def action_send(self):
        self.write({'schedule_type': 'now'})
        return self.action_put_in_queue()
    
    def action_cancel(self):
        self.write({'state': 'draft', 'schedule_date': False, 'schedule_type': 'now'})

    def action_schedule(self):
        self.ensure_one()
        if self.schedule_date and self.schedule_date > fields.Datetime.now():
            return self.action_put_in_queue()
        action = self.env["ir.actions.actions"]._for_xml_id("zalo_connector.schedule_date_action")
        action['context'] = dict(self.env.context, default_campaign_id=self.id, dialog_size='medium')
        return action
        
    def action_put_in_queue(self):
        self.write({'state': 'in_queue'})
        cron = self.env.ref('zalo_connector.ir_cron_zalo_campaign_queue')
        cron._trigger(
            schedule_date or fields.Datetime.now()
            for schedule_date in self.mapped('schedule_date')
        )
    
    @api.model
    def _process_queue(self):
        # Search for messages in the queue or currently sending
        messages = self.search([('state', '=', 'in_queue')])
        for message in messages:
            if message:
                message.schedule_date = fields.Datetime.now()
                message.zns_template_message()
                message.state = 'done'
            else:    
                message.write({
                    'state': 'done',
                    'sent_date': fields.Datetime.now(),
                })

    def zns_template_message(self):
        # Create ZNS Template Campaign
        domain_records = self.env[self.model_id.model].search(literal_eval(self.domain))
        for rec in domain_records:
            zns_template_vals = []
            for key_field in self.zns_template.template_data:
                if key_field.field_type.ttype == 'many2one':
                # Assuming the field type is a Many2one field
                    related_record = getattr(rec, key_field.field_type.name)
                    if related_record:
                        field_value = related_record.name 
                else:
                    field_value = getattr(rec, key_field.field_type.name, False)
                val = {
                    'name': key_field.name, 
                    'value':  str(field_value) if field_value else '' 
                }
                zns_template_vals.append((0, 0, val))
            messages = self.env['zns.messages'].sudo().create({
                'number': re.sub(r'^0', '+84', rec.partner_id.phone) if rec.partner_id.phone else '',
                'template_id': self.zns_template.zns_template_id,
                'body': self.zns_template.name,
                'zns_template_val_ids': zns_template_vals,
                'campaign_id': self.id
            })
        return messages

    
          