from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    zalo_oa_name = fields.Char("Zalo OA")
    zalo_app_id = fields.Char("Zalo App ID")
    zalo_secret_key = fields.Char("Zalo Secret Key")
    zalo_callback_url = fields.Char("Zalo Callback URL")
    zalo_link_api = fields.Char("Zalo API", default='https://oauth.zaloapp.com/v4/oa/access_token')
    zalo_oa_id = fields.Many2one(
        related="company_id.zalo_oa_id", string="Zalo OA", ondelete='cascade',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]" , readonly=False)
    company_template_id = fields.Many2one(
        related="company_id.zns_rating_template_id", string="ZNS Template", readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(zalo_oa_name=self.env["ir.config_parameter"].sudo().get_param("zalo_oa_name"),
                   zalo_app_id=self.env["ir.config_parameter"].sudo().get_param("zalo_app_id"),
                   zalo_secret_key=self.env["ir.config_parameter"].sudo().get_param("zalo_secret_key"),
                   zalo_callback_url=self.env["ir.config_parameter"].sudo().get_param("zalo_callback_url"),
                   zalo_link_api=self.env["ir.config_parameter"].sudo().get_param("zalo_link_api"),)
        return res
    
    def set_values(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("zalo_oa_name", self.zalo_oa_name)
        params.set_param("zalo_app_id", self.zalo_app_id)
        params.set_param("zalo_secret_key", self.zalo_secret_key)
        params.set_param("zalo_callback_url", self.zalo_callback_url)
        params.set_param("zalo_link_api", "https://oauth.zaloapp.com/v4/oa/access_token")
        return super(ResConfigSettings, self).set_values()

    def zalo_authorization_code(self):
        return self.env["zalo.oa"].get_authorization_code()
