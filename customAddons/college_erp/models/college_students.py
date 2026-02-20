from datetime import date
from dateutil.utils import today
from odoo import fields,models,api
from odoo.exceptions import ValidationError
class collegeStudent(models.Model):
    _name="college.student"
    _description= "College Student"
    _order = "first_name desc"
    _rec_name="first_name"
    _sql_constraints=[
        ('personal_number_unique',
          'unique(personal_number)',
           'შეცდომა: სტუდენტი ამ პირადი ნომრით უკვე არსებობს')
    ]

    personal_number=fields.Char(string="Personal Number")
    born_date=fields.Date(string="Born Date")
    age=fields.Integer(string="Age",compute='_compute_age',store=True)
    entery_date=fields.Date(string="entery Date")
    first_name=fields.Char(string="First Name")
    last_name=fields.Char(string="Last Name")
    father_name = fields.Char(string="Father's Name")
    mother_name = fields.Char(string="Mother's Name")
    coomunication_addr=fields.Text(string="Communication Addres")
    street=fields.Char(string="Street")
    street2=fields.Char(string="Street2")
    zip=fields.Char(string="Zip")
    city=fields.Char(string="City")
    state_id=fields.Many2one(comodel_name='res.country.state',string="Fed.State",domain="[('country_id','=?',country_id)]")
    country_id=fields.Many2one(comodel_name='res.country')
    email=fields.Char(string="Mail")
    phone=fields.Char(string="Phone")
    same_as_communication= fields.Boolean(string="Same as Communication", default=True)
    image_1920=fields.Image(string="Upload Student's image")
    gender=fields.Selection([('male','Male'),('female','Female')],string="Gender")
    active=fields.Boolean(string="active")
    status=fields.Selection([('active','Active'),('nonactive','Nonactive')],string="Status", default="active")





    @api.depends('born_date')
    def _compute_age(self):
        for rec in self:
            if rec.born_date:
                today=date.today()
                rec.age = today.year - rec.born_date.year - ((today.month, today.day) < (rec.born_date.month, rec.born_date.day))
            else:

                rec.age=0
    @api.constrains('born_date','personal_number','phone')
    def _check_student_data(self):
        for rec in self:
            if rec.personal_number:
                if len(rec.personal_number) !=11 and not rec.personal_number.isdigit():
                    raise ValidationError("პირადი ნომერი უნდა შედგებოდეს 11 ციფრისაგან და არ შეიძლება სიმბოლოების დაწერა,შეიყვანეთ მხოლოდ 11 ციფრი!")
            if rec.born_date:
                if rec.age < 18:
                    raise ValidationError("არასრულწლოვანის რეგისტრაცია დაუშვებელია")

            if rec.phone and not rec.personal_number.isdigit():
                raise  ValidationError("ტელეფონი უნდა შეიცავდეს მხოლოდ რიცხვებს")



    def action_test(self):
        print("Clicked Succsesfull!!!")
        return {
            'effect': {
                'fadeout':'slow',
                'message':'Click succesfull',
                'type':'rainbow_man',
            }
        }