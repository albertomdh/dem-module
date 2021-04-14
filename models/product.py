from odoo import models, fields, exceptions, _
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class ProductInheritProductStockPriceConnector(models.Model):
    _inherit = 'product.template'

    def send_product_template_info(self):
        headers = {'Content-Type': 'application/json'}
        for line in self:
            variants = line.product_variant_ids
            product_images = []
            variant_data = []
            if line.image_medium:
                product_images.append(line.image_medium.decode('utf-8'))
            for variant in variants:
                variant_data.append({
                    'sku': variant.default_code, 
                    'sales_price': variant.list_price, 
                    'stock':variant.qty_available_not_res,
                    'barcode': variant.barcode,
                    'taxable': bool(variant.taxes_id),
                    'shopify_variant_id': variant.shopify_variant_id
                    'variant_info':[{variant_attribute.attribute_id.display_name: variant_attribute.name} for
                                     variant_attribute in
                                     variant.attribute_value_ids]
                })
                if variant.image_medium:
                    product_images.append(variant.image_medium.decode('utf-8'))
            data = {
                "name": line.name,
                "image": product_images,
                "description": line.website_description,
                "vendor": line.marca_ids.mapped('display_name'),
                "variants": variant_data,
                "tags": self.get_product_parent_tags(),
            }
            data_json = json.dumps({'params': data})
            try:
                product_stock_price_connector_server = self.env.user.company_id.product_stock_price_post_server
                requests.post(url=product_stock_price_connector_server, data=data_json, headers=headers)
            except Exception as e:
                raise exceptions.ValidationError(_("Failed to send post request for the product %s, reason : %s" % (
                    line.name, e)))
                
    def write(self, vals):
        print(vals)
        res = super(ProductInheritProductStockPriceConnector, self).write(vals)
        if vals.get('list_price'):
            self.send_new_price_data_product_connector_webserver()
        return res
 
    def send_new_price_data_product_connector_webserver(self):
        for line in self:
            variants = line.product_variant_ids
            for variant in variants:
                data = {'sku': variant.default_code,
                        'new_stock': variant.qty_available,
                        'new_price': variant.list_price}
                print(data)
                headers = {'Content-Type': 'application/json'}
                data_json = json.dumps({'params': data})
                try:
                    requests.post(url=self.env.user.company_id.product_stock_price_post_server, data=data_json,
                                  headers=headers)
                except Exception as e:
                    _logger.error("Failed to send post request to webservice, reason : %s" % e)
                 
    def get_product_parent_tags(self):
        res_categ = []
        for categs in self.public_categ_ids:
            res_categ.append(categs.display_name.split('/'))
        if res_categ:
            if len(res_categ) <= 1:
                res_categ = res_categ[0]

        return res_categ
    
# class ProductProductStockPriceConnector(models.Model):
#     _inherit = 'product.product'
#
#     def write(self, vals):
#         print(vals)
#         res = super(ProductProductStockPriceConnector, self).write(vals)
#         if vals.get('lst_price'):
#             self.send_new_price_data_product_connector_webserver()
#         return res
#
#     def send_new_price_data_product_connector_webserver(self):
#         for line in self:
#             data = {'sku': line.product_id.default_code,
#                     'new_stock': line.product_id.qty_available,
#                     'new_price': line.product_id.list_price}
#             headers = {'Content-Type': 'application/json'}
#             data_json = json.dumps({'params': data})
#             print(data)
#             try:
#                 requests.post(url=self.env.user.company_id.product_stock_price_post_server, data=data_json,
#                               headers=headers)
#             except Exception as e:
#                 _logger.error("Failed to send post request to webservice, reason : %s" % e)
