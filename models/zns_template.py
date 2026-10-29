from odoo import api, models, fields, _
import json
import logging
import requests
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class ZNSTemplate(models.Model):
    _name = 'zns.template'
    _description = 'ZNS Template'

    name = fields.Char()
    zns_template_id = fields.Char(string='Template ID')
    model_id = fields.Many2one(
        'ir.model', string='Applies to', required=True,
        help="The type of document this template can be used with", ondelete='cascade')
    template_data = fields.One2many('zns.template.line', 'zns_template_id', string='Template Data')
    status = fields.Selection(selection=[('enable', 'Enable'), ('pending_review', 'Pending Review')], string='Status', default='enable', required=True)
    company_id = fields.Many2one('res.company')
    preview_url = fields.Char('Preview Url', readonly=True)
    zalo_oa_id = fields.Many2one('zalo.oa', string='Zalo OA')
    
    def get_template_details(self, raise_exception=True):
        url = 'https://business.openapi.zalo.me/template/info?template_id=%s' % self.zns_template_id
        zalo_oa = self.env['zalo.oa'].search([])
        if not zalo_oa:
            if raise_exception:
                raise UserError('Zalo OA not found')
            else:
                return

        access_token = zalo_oa[0].access_token
        headers = {
            'access_token': access_token,
        }
        # import pdb; pdb.set_trace();
        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()
            print(response_data)
            if response_data.get('error', False):
                if raise_exception:
                    raise UserError(response_data.get('message'))
                else:
                    return        
            template_data = response_data.get('data', {})
            name = template_data.get('templateName', [])
            preview_url = template_data.get('previewUrl', [])

            # Update or create zns.template record with templateName
            template_record = self.env['zns.template'].search([])
            if template_record:
                template_record.write({
                    'name': name,
                    'preview_url': preview_url
                })  

            list_params = template_data.get('listParams', [])
            template_lines = []
            for param in list_params:
                name = param.get('name')
                if name:
                    template_lines.append((0, 0, {'name': name}))
            self.write({'template_data': template_lines})
        except Exception as e:
            error_message = "Get template failed"           
        

    def get_sample_data_of_template(self):
        url = ' https://business.openapi.zalo.me/template/sample-data'
        zalo_oa = self.env['zalo.oa'].search([])
        if zalo_oa:
            access_token = zalo_oa[0].access_token
            headers = {
                'access_token': access_token,
                'Content-Type': 'application/json'
            }
            data = {
                'template_id': self.zns_template_id
            }
            try:
                response = requests.post(url, headers=headers, json=data)
                return response.json()
            except Exception as e:
                _logger.info("Get sample data template failed")
        else:
            _logger.info('Zalo OA not found') 

    def open_preview_url(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.preview_url,
            'target': 'new',
        }
            

class ZNSTemplateLine(models.Model):
    _name = 'zns.template.line'
    _description = 'ZNS Template Line'

    name = fields.Char()
    value = fields.Char()
    field_map = fields.Char()
    model_id = fields.Many2one(related='zns_template_id.model_id')
    field_type = fields.Many2one('ir.model.fields', string="Field Map")
    zns_template_id = fields.Many2one('zns.template')
    message_id = fields.Many2one('zns.messages')

 



        


    




    
    
    

