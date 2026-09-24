
from odoo import models,fields


class HotelService(models.Model):
    _name="hotel.service"
    _description="Hotel Service"

    name=fields.Char(string="Service Name", required=True)
    service_type=fields.Selection([('food','Food & Beverage'),('transport','Transportation'),('spa','SPA & Wellness'),('laundry','Laundry & Cleaning'),('other','Other')],default='food',required=True)
    price=fields.Float(string="Price", required=True, default=0.0)
    active=fields.Boolean(string="Active", default=True)
    description=fields.Text(string="Description")
