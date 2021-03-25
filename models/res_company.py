from odoo import models, fields


class ResCompanyInheritProductStockPriceConnector(models.Model):
    _inherit = 'res.company'

    product_stock_price_post_server = fields.Char()
    dummy_sale_order_customer = fields.Many2one('res.partner', string="Dummy customer",
                                                help="Assign this customer to the sale order received if no partner found")
