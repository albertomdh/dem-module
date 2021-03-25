# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import http, tools, exceptions, _

_logger = logging.getLogger(__name__)
from odoo.http import request
import json


class ProductStockPriceConnector(http.Controller):

    @http.route(["/create_sale_order_connector"], type='json', auth="user", methods=['POST'])
    def synchronise_odoo(self, **post):
        _logger.info("Post request received")
        _logger.info("Creating sale order...")
        # get the partner, if not found create new one with the given id
        try:
            if not request.httprequest.get_data():
                _logger.info("No data found, Abort")
            converted_data = json.loads(request.httprequest.get_data().decode('utf-8'))
            data = converted_data
            if not data:
                _logger.info("No data found, Abort")
                return
            partner_id = data.get('id')
            if not partner_id:
                _logger.info("Partner not found in the post json, Abort")
            partner_odoo = request.env['res.partner'].browse(partner_id)
            if partner_odoo.exists():
                partner = partner_odoo
            else:
                _logger.info("Customer not found at the database, assigning dummy customer ...")
                partner = request.env.user.company_id.dummy_sale_order_customer
                if not partner:
                    _logger.info("No dummy customer found, aborting the request ...")
                    return
            # get the sale lines

            order_lines = data.get('order_lines')
            if order_lines:
                order_line = self.get_sale_order_line_data(order_lines)
            else:
                order_line = []

            request.env['sale.order'].create(
                {'partner_id': partner.id, 'order_line': order_line}, )
        except Exception as e:
            _logger.info("Error occurred while executing the logic %s" % e)

    def get_sale_order_line_data(self, order_line_data):
        res = []
        for line in order_line_data:
            product_id = request.env['product.product'].sudo().search([('default_code', '=', line['sku'])], limit=1)
            if product_id:
                res.append((0, 0, {'product_id': product_id.id, 'product_uom_qty': line.get('quantity'), }))
        return res
