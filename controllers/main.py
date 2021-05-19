# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import http, tools, exceptions, _

_logger = logging.getLogger(__name__)
from odoo.http import request
import json


class ProductStockPriceConnector(http.Controller):

    @http.route(["/create_sale_order_connector"], type='json', auth="none", methods=['POST'])
    def synchronise_odoo(self, **post):
        _logger.info("Post request received")
        _logger.info("Creating sale order...")
        
        #Expected object
        #{lo del webook, idDist}

        # get the partner, if not found create new one with the given id
        
        try:
            if not request.httprequest.get_data():
                _logger.info("No data found, Abort")
            converted_data = json.loads(request.httprequest.get_data().decode('utf-8'))
            data = converted_data
            if not data:
                _logger.info("No data found, Abort")
                return
            
            #Geting request variables
            sale_order_id = data.get('id');
            partner_id = data.get('idDist');
            customer_shopify_id = data.get('customer');
            customer_billing_address = data.get('billing_address')
            customer_shipping_address = data.get('shipping_address');
            shopify_note = data.get("note") or "";
            shopify_note = "Nota de Envio: " + shopify_note;
            phone_customer = customer_shopify_id.get('default_address').get('phone')
            customer_odoo = request.env['res.partner'].sudo().search(
                [('email', '=', customer_shopify_id.get('id'))])
            
            #Creating or updating customer
            if customer_odoo.exists():
                _logger.info("Customer found at odoo.")
                customer = customer_odoo
                customer.over_credit = True
                customer.phone = phone_customer
                _logger.info("Customer Phone: %s" % phone_customer )
            else:
                _logger.info("Customer not found at odoo, creating new one ...")
                _logger.info("Customer Phone: %s" % phone_customer )
                customer = request.env['res.partner'].sudo().create(
                    {'name':customer_shopify_id.get('first_name') + " " + customer_shopify_id.get('last_name') ,
                     'shopify_client_id': customer_shopify_id.get('id'),
                     'customer': True,
                     'vat': customer_billing_address.get('company'),
                     'email': customer_shopify_id.get('email'),
                     'street_name': customer_billing_address.get('address1'),
                     'zip': customer_billing_address.get('zip'),
                     'city': customer_billing_address.get('city'),
                     'over_credit': True,
                     'phone': phone_customer
                    })

            #Assigning Dist Partner
            if not partner_id:
                _logger.info("Dist not found in the post json, Abort")
            partner_odoo = request.env['res.partner'].browse(partner_id)

            if partner_odoo.exists():
                partner = partner_odoo
            else:
                _logger.info("Dist not found at the database, assigning dummy partner ...")
                partner = request.env.user.company_id.dummy_sale_order_customer
                if not partner:
                    _logger.info("No dummy dist found, aborting the request ...")
                    return

            # creating disscount
            order_lines = data.get('line_items')

            subtotal_without_taxes_shopify = float(data.get('subtotal_price')) - float(data.get('total_tax'));
            discount = self.get_discount_order_line_data(order_lines, subtotal_without_taxes_shopify);

            if discount < 15:
                discount = 15

            # get the sale lines
            if order_lines:
                _logger.info("DEM: Hay order_lines")
                order_line = self.get_sale_order_line_data(order_lines, discount)
            else:
                order_line = []

        #    request.env['sale.order'].create(
        #        {'partner_id': partner.id, 'order_line': order_line}, )

            shipping_title = "Recoger en Tienda"
            shopify_shipping_lines = data.get('shipping_lines')
            if shopify_shipping_lines:
                shipping_title = shopify_shipping_lines[0].get('title')

            it_was_gift_card = False
            for gateway_name in data.get('payment_gateway_names'):
                if gateway_name == 'gift_card':
                    it_was_gift_card = True

            sale_order = request.env['sale.order'].sudo().create(
                {
                    'partner_id': customer.id,
                    'partner_invoice_id': partner.id,
                    'partner_shipping_id': customer.id,
                    'order_line': order_line,
                    'portal': 'DEM ' + data.get('name'),
                    'x_studio_metodo_de_pago': data.get('gateway'),
                    'x_studio_metodo_de_envio_shopify': shipping_title,
                    'x_studio_comentarios': shopify_note,
                    'x_studio_pago_con_gift_cards': it_was_gift_card,
                    'shopify_sale_order_id': sale_order_id
                }, )
            _logger.info("Confirming the created sale")

            #las siguientes 5 lineas no se bien que pedo
            sale_order.message_post(body=shopify_note)
            try:
                sale_order.action_confirm()
            except Exception as e:
                _logger.info("Error occurred while confirming the sale %s" % e)

        except Exception as e:
            _logger.info("Error occurred while executing the logic %s" % e)

    def get_sale_order_line_data(self, order_line_data, discount):
        res = []
        for line in order_line_data:
            product_dis = 0
            product_id = request.env['product.product'].sudo().search([('default_code', '=', line['sku'])], limit=1)
            
            if product_id:
                product_dis = ( 1 - ( float(line.get('price')) / float(product_id.list_price) ) )  * 100            
                if product_dis < 15:
                    product_dis = 15
                _logger.info("DEM: Appending product to order")
                res.append((0, 0, {'product_id': product_id.id, 'product_uom_qty': line.get('quantity'), 'discount': product_dis}))
        return res

    def get_discount_order_line_data(self, order_line_data, shopify_total):
        total_tax_not_included = float(0)
        discount = float(0)
        for line in order_line_data:
            product_odoo = request.env['product.product'].sudo().search([('default_code', '=', line['sku'])], limit=1)
            if product_odoo:
                total_tax_not_included += float(product_odoo.list_price) * int(line.get('quantity'))
        
        _logger.info("Shopify Total: %f" % shopify_total)
        _logger.info("Odoo Estimate: %f" % total_tax_not_included)

        if shopify_total < total_tax_not_included:
            discount = (1 - (shopify_total / total_tax_not_included )) * 100
            _logger.info("A discount it must be in the line order. Discount: %f" % discount)
        return discount
