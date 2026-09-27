
from odoo import models,fields


class HotelService(models.Model):
    _name="hotel.service"
    _description="Hotel Service"

    name=fields.Char(string="Service Name", required=True)
    service_type=fields.Selection([('food','Food & Beverage'),('transport','Transportation'),('spa','SPA & Wellness'),('laundry','Laundry & Cleaning'),('other','Other')],default='food',required=True)
    currency_id=fields.Many2one('res.currency', string='Currency',default=lambda self:self.env.company.currency_id ,readonly=True)
    price=fields.Monetary(string="Price",currency_field='currency_id',required=True, default=0.0)
    active=fields.Boolean(string="Active", default=True)
    description=fields.Text(string="Description")

