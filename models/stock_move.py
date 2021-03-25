from odoo import models, fields, api, _
import requests
import json
import logging

_logger = logging.getLogger(__name__)
from odoo.tools.float_utils import float_is_zero
from odoo.tools.pycompat import izip


class StockMoveLineInheritProductStockPriceConnector(models.Model):
    _inherit = 'stock.move.line'

    def send_new_stock_data_product_connector_webserver(self):
        for line in self:
            data = {'sku': line.product_id.default_code,
                    'new_stock': line.product_id.qty_available,
                    'new_price': line.product_id.list_price}
            headers = {'Content-Type': 'application/json'}
            print(data)
            data_json = json.dumps({'params': data})
            try:
                requests.post(url=self.env.user.company_id.product_stock_price_post_server, data=data_json, headers=headers)
            except Exception as e:
                _logger.error("Failed to send post request to webservice, reason : %s" % e)

    def _action_done(self):
        res = super(StockMoveLineInheritProductStockPriceConnector, self)._action_done()
        for stock_move_line in self:
            stock_move_line.send_new_stock_data_product_connector_webserver()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """A function like create of the original in order to track the changing of done moves qty"""
        mls = super(StockMoveLineInheritProductStockPriceConnector, self).create(vals_list)
        for ml, vals in izip(mls, vals_list):
            if ml.state == 'done':
                if ml.product_id.type == 'product':
                    ml.send_new_stock_data_product_connector_webserver()
        return mls

    def write(self, vals):
        """ A write function like in the original to update products qtys in case of modification in done state of move
        """
        res = super(StockMoveLineInheritProductStockPriceConnector, self).write(vals)
        triggers = [
            ('location_id', 'stock.location'),
            ('location_dest_id', 'stock.location'),
            ('lot_id', 'stock.production.lot'),
            ('package_id', 'stock.quant.package'),
            ('result_package_id', 'stock.quant.package'),
            ('owner_id', 'res.partner')
        ]
        updates = {}
        for key, model in triggers:
            if key in vals:
                updates[key] = self.env[model].browse(vals[key])

        if updates or 'qty_done' in vals:

            mls = self.filtered(lambda ml: ml.move_id.state == 'done' and ml.product_id.type == 'product')
            if not updates:  # we can skip those where qty_done is already good up to UoM rounding
                mls = mls.filtered(lambda ml: not float_is_zero(ml.qty_done - vals['qty_done'],
                                                                precision_rounding=ml.product_uom_id.rounding))
            for ml in mls:
                ml.send_new_stock_data_product_connector_webserver()
        return res
