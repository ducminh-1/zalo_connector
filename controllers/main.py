import base64
import json
import logging
import re

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.web.controllers.main import Home




class ZaloHome(http.Controller):
    @http.route("/zalo/authorization-code", type="http", auth="public", website=True)
    def authorized_code(self, redirect=None, **data):
        if data.get("code"):
            zalo_oa_id = data.get("oa_id")
            code = data.get("code")
            if code and code != "":
                return request.env["zalo.oa"].create_access_token(code, zalo_oa_id, data)
        elif data.get("error", False):
            raise UserError(data.get("error"))
        else:
            raise UserError(_("Auth code is invalid!"))
        return True
    
    