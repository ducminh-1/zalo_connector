from datetime import datetime,timedelta,timezone
import hashlib
import hmac
import requests
import traceback
import logging
import json
from datetime import datetime
from urllib.parse import urlencode
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode, url_join
import werkzeug
import base64

from odoo import fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError

TRANSACTION_TYPE_METHOD = {
    'get_access_token': 'post',
    'refresh_access_token': 'post',
    'get_authorization_code': 'post',
    'send_message': 'post',
 }


class ZaloOA(models.Model):
    _name = 'zalo.oa'
    _description = 'zalo chat authen api'
    _base_url = 'https://openapi.zalo.me'
    _auth_url = 'https://oauth.zaloapp.com/v4/oa/access_token'

    name = fields.Char('Zalo OA', required=True)
    access_token = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('disconnected', 'Disconnected'),
        ('connected', 'Connected'),
        ('error_occurred', 'Error')
    ], string='State', default='draft', tracking=True)
    access_token_expired_date = fields.Datetime()
    refresh_token = fields.Char(copy=False)
    refresh_token_expired_date = fields.Datetime()
    app_id = fields.Char('App ID')
    secret_key = fields.Char('Secret Key')
    auth_code = fields.Char() 
    code = fields.Char()
    zalo_oa_id = fields.Char()
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    transaction_ids = fields.One2many(
        comodel_name="zalo.oa.transaction",
        inverse_name="zalo_oa_id",
        readonly=True,
    )

    def _make_request(self, transaction_type=None, url=None, headers=None, data=None, raise_if_error=False):
        self.ensure_one()
        url = url or self._base_url
        data = data or {}
        headers = headers or {}
        response = False
        error_message = ""
        try:
            # Make the API request
            kwargs = {}
            if data:
                kwargs["data"] = (data) 
            if headers:
                kwargs["headers"] = headers
            data.update(is_success=False)
            logging.info(f"Calling Zalo request: {TRANSACTION_TYPE_METHOD}")
            logging.info(url)
            logging.info(kwargs)
            response = getattr(requests, TRANSACTION_TYPE_METHOD[transaction_type])(
                url, **kwargs
            )
            # Check the response status code
            if response.status_code == 200:
                data = response.json()
                # Not successful response
                if data.get("error") == 0:
                    data["is_success"] = False
                    error_message = data.get("error", "")
                # Successful response
                else:
                    data["is_success"] = True
            else:
                # Handle non-200 status codes
                logging.error(traceback.format_exc())
                error_message = (
                    f"Request failed with status code: {response.status_code}"
                )
                logging.error(error_message)

        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors (status codes 4xx and 5xx)
            logging.error(traceback.format_exc())
            logging.error(f"HTTP Error occurred: {str(e)}")
            logging.error(f"Response content: {response.text}")
            error_message = str(e)
        except requests.exceptions.RequestException as e:
            # Handle connection errors, timeouts, or other request exceptions
            logging.error(traceback.format_exc())
            logging.error(f"An error occurred during the request: {str(e)}")
            error_message = str(e)
        except ValueError as e:
            # Handle JSON decoding errors
            logging.error(traceback.format_exc())
            logging.error(f"Error occurred while decoding JSON: {str(e)}")
            error_message = str(e)
            logging.error(f"Response content: {response.text}")
        except Exception as e:
            # Handle other unexpected exceptions
            logging.error(traceback.format_exc())
            logging.error(f"An unexpected error occurred: {str(e)}")
            error_message = str(e)

        if error_message:
            if raise_if_error:
                raise UserError(error_message)
            data["error_message"] = error_message
        return (
            self.transaction_ids.sudo().create(
                {
                    "zalo_oa_id": self.id,
                    "json_data": json.dumps(data, sort_keys=True, indent=4),
                    "is_success": data["is_success"],
                    "transaction_type": transaction_type,
                }
            ),
            data,
        )
    

    def send_message(self):
        headers = {"access_token": self.access_token}
        body= {
            "recipient": {
                "user_id": "637969452697036124"
            },
            "message": {
                "text": "hello world"
            }
        }
        return self._make_request(
            url=f"{self._base_url}/v3.0/oa/message/cs",
            transaction_type="send_message",
            headers=headers,
            data=body,      
        )
    
    def _display_notification(self, message_type, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": message_type,
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
                "context": dict(self._context, active_ids=self.ids),
            },
        }

    def action_get_access_token_by_auth_code(self):
        self.ensure_one()
        return self._get_access_token(
            {
                "code": self.auth_code,
                "grant_type": "authorization_code",
            },
            "get_authorization_code",
            "Get access token successful!",
        )

    def action_refresh_access_token(self):
        self.ensure_one()
        return self._get_access_token(
            {
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            "refresh_access_token",
            "Refresh access token successful!",
        )
    
    def _get_access_token(self, extra_params, transaction_type, success_msg):
        self.ensure_one()
        header_queries = {"secret_key": self.secret_key}
        body_queries = {"app_id": self.app_id, **extra_params}
        _transaction, data = self._make_request(
            transaction_type=transaction_type,
            url=f"{self._auth_url}",
            headers=header_queries,
            data=body_queries
        )
        if data.get("is_success"):
            self.write(
                {
                    "access_token": data["access_token"],
                    "refresh_token": data["refresh_token"],
                    "access_token_expired_date": fields.Datetime.now() + relativedelta(seconds=int(data["expires_in"])),
                    "refresh_token_expired_date": fields.Datetime.now() + relativedelta(months=3)
                }
            )
            return self._display_notification("success", _(success_msg))
        else:
            return self._display_notification("warning", data.get("error_message"))


    def get_authorization_code(self):
        ZaloConfig = self.env['res.config.settings'].get_values()   
        app_id = ZaloConfig.get('zalo_app_id')
        callback_url = ZaloConfig.get('zalo_callback_url')  
        action_url = "https://oauth.zaloapp.com/v4/oa/permission"
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        params = {
            "app_id": app_id,
            "redirect_uri": callback_url,
        }
        url = "%s?%s" % (action_url, url_encode(params))
        return {
            "name": "auth.zalo",
            "res_model": "ir.actions.act_url",
            "type": "ir.actions.act_url",
            "target": "new",
            "url": url,
        }
        

    def create_access_token(self, code, zalo_oa_id, data):
        if not code or code == "":
            raise UserError(_("Please enter code!"))
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        ZaloConfig = self.env['res.config.settings'].get_values()     
        name = ZaloConfig.get('zalo_oa_name')
        app_id = ZaloConfig.get('zalo_app_id')
        secret_key = ZaloConfig.get('zalo_secret_key')
        code = data.get('code')
        zalo_oa_id = data.get('oa_id')
        zalo_oa = self.env['zalo.oa'].sudo().search([("zalo_oa_id", "=", zalo_oa_id)], limit=1)
        if zalo_oa:
            self.write({
                "zalo_oa_id": zalo_oa_id,
                "app_id": app_id,
                "secret_key": secret_key,
                "link_callback_url": self.link_callback_url,
                "auth_code": code
            })
           
        else:
            zalo_oa = self.env["zalo.oa"].sudo().create({
                "name": name,
                "zalo_oa_id": zalo_oa_id,
                "app_id": app_id,
                "secret_key": secret_key,
                "auth_code": code
            })
        try:
            if zalo_oa:
                zalo_oa.action_get_access_token_by_auth_code()
                zalo_oa.write({'state': 'connected'})
        except Exception as e:
            pass  
        return werkzeug.utils.redirect(
            "%s/web#id=%s&menu_id=%s&action=%s&model=zalo.oa&view_type=form" % (
                base_url,
                zalo_oa.id,
                self.env.ref('zalo_connector.zalo_oa_menu').id,
                self.env.ref('zalo_connector.zalo_oa_action').id,
            )
        )
        
    def auto_refresh_token(self):
        zalo_oa_ids = self.search([('access_token_expired_date', '<=', datetime.now() + timedelta(hours=24))])
        for zalo_oa_id in zalo_oa_ids:     
            zalo_oa_id.action_refresh_access_token()

    def get_user_profile(self, user_id, raise_exception=True):
        if not user_id:
            return '', False
        partner_id = self.env['res.partner'].search([('zalo_user_id', '=', user_id)], limit=1) 
        if not partner_id:
            access_token = self.access_token
            url = 'https://openapi.zalo.me/v2.0/oa/getprofile?data={"user_id":"%s"}' % user_id.replace(' ','')
            header = {
                'access_token': access_token,
            }
            resp = requests.get(url=url, headers=header)
            resp_json = resp.json()
            if resp_json.get('error', False):
                if raise_exception:
                    raise UserError(resp_json.get('message'))
                else:
                    return ''

            # get avatar
            avatar_url = resp_json['data'].get('avatars',[]) and resp_json['data']['avatars'].get('240','') or resp_json['data'].get('avatar','')
            avatar = ''
            if avatar_url:
                avatar_request = requests.get(avatar_url)
                avatar = avatar_request.content
            # create contact
            partner_id = self.env['res.partner'].create({
                'name': resp_json['data'].get('display_name', user_id),
                'image_1920': base64.b64encode(avatar),
                'zalo_user_id': user_id,
            })
        return partner_id
    


    