# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ScheduleDate(models.TransientModel):
    _name = "schedule.date.campaign"
    _description = "schedule a campaign"

    schedule_date = fields.Datetime(string='Scheduled Date')
    campaign_id = fields.Many2one('zns.campaign', required=True)

    def action_schedule_date(self):
        self.campaign_id.write({'schedule_type': 'scheduled', 'schedule_date': self.schedule_date})
        self.campaign_id.action_put_in_queue()