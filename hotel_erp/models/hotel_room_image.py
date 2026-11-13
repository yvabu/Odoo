from odoo import fields,models

class hotelRoomImages(models.Model):
    _name='hotel.room.images'
    _description='Hotel Room Images'

    name=fields.Char(string="Photo Title/Description")
    image_1920=fields.Image(string="Image",max_width=1920,max_height=1920,verify_resolution=False)
    room_id=fields.Many2one('hotel.room',string="Room",ondelete='cascade')