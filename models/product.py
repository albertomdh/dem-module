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
                variant_info_array=[]
                for variant_attribute in variant.attribute_value_ids:
                    variant_info_array.append({variant_attribute.attribute_id.display_name: variant_attribute.name})
                variant_data.append({'sku': variant.default_code, 'sales_price': variant.list_price, 'stock':variant.qty_available_not_res, 'variant_info':variant_info_array})
                if variant.image_medium:
                    product_images.append(variant.image_medium.decode('utf-8'))
            res_categ = []
            for categs in self.public_categ_ids:
                res_categ.append(categs.display_name.split('/'))
            if res_categ:
                if len(res_categ) <= 1:
                    res_categ = res_categ[0]
            data = {
                "name": line.name,
                "image": product_images,
                "description": line.website_description,
                "vendor": line.marca_ids.mapped('display_name'),
                "variants": variant_data,
                "tags":res_categ
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
