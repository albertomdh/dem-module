from odoo import models, fields, api, exceptions, _

import requests
import json
import logging

_logger = logging.getLogger(__name__)


class ResPartnerInheritProductStockConnector(models.Model):
    _inherit = "res.partner"

    def send_partner_info(self):
        for line in self:
            partner_id = line.id
            address = "%s %s,%s %s %s,%s" % (line.street, line.street2, line.city, line.state_id.name,
                                             line.zip, line.country_id.name)
            partner_name = line.name
            partner_vat = line.vat
            partner_phone = line.mobile
            partner_email = line.email
            client_number = line.ncliente

            data = {"id": partner_id, "address": address, "name": partner_name, "vat": partner_vat,
                    "phone": partner_phone, "email": partner_email,
                    "client_number": client_number}
            print(data)
            headers = {'Content-Type': 'application/json'}
            data_json = json.dumps({'params': data})
            try:
                requests.post(url=self.env.user.company_id.product_stock_price_post_server, data=data_json,
                              headers=headers)
            except Exception as e:
                raise exceptions.ValidationError(
                    _("Failed to send partner information for the partner %s, reason : %s" % (line.name, e)))
