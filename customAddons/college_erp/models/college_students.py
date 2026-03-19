from datetime import date
from dateutil.utils import today
from docutils.nodes import status

from odoo import fields,models,api
from odoo.exceptions import ValidationError
class CollegeStudent(models.Model):
    _name="college.student"
    _description= "College Student"
    _order = "id desc"
    _rec_name="user_id"
    _sql_constraints=[
        ('personal_number_unique',
          'unique(personal_number)',
           'შეცდომა: სტუდენტი ამ პირადი ნომრით უკვე არსებობს'
        )
    ]
    mark_ids = fields.One2many('college.mark','student_id')
    subject_ids=fields.Many2many('college.subjects', string="Subjects")
    user_id=fields.Many2one('res.users',string="User",readonly=True)
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
    email=fields.Char(string="Mail",compute="_compute_email")
    phone=fields.Char(string="Phone")
    same_as_communication= fields.Boolean(string="Same as Communication", default=True)
    image_1920=fields.Image(string="Upload Student's image")
    gender=fields.Selection([('male','Male'),('female','Female')],string="Gender")
    active=fields.Boolean(string="active")
    status=fields.Selection([('active','Active'),('nonactive','Nonactive')],string="Status", default="active")


    @api.depends('email')
    def _compute_email(self):
        for rec in self:
            rec.email=f"{rec.first_name}.{rec.last_name}@kolkheti.edu"
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
                if len(rec.personal_number) !=11 or not rec.personal_number.isdigit():
                    raise ValidationError("პირადი ნომერი უნდა შედგებოდეს 11 ციფრისაგან და არ შეიძლება სიმბოლოების დაწერა,შეიყვანეთ მხოლოდ 11 ციფრი!")
            if rec.born_date:
                if rec.age < 18:
                    raise ValidationError("არასრულწლოვანის რეგისტრაცია დაუშვებელია")

            if rec.phone:
                if not rec.phone.isdigit():
                    raise ValidationError("ტელეფონი უნდა შეიცავდეს მხოლოდ რიცხვებს")



    def translate_to_Active(self):
        for rec in self:
            rec.status=("active")

    def translate_to_Nonactive(self):
        for rec in self:
            rec.status=("nonactive")



    def action_test(self):
        print("Clicked Succsesfull!!!")
        return {
            'effect': {
                'fadeout':'slow',
                'message':'Click succesfull',
                'type':'rainbow_man',
            }
        }
    def create(self,vals):
        #1.სტუდენტის ჩანაწერის შექმნა ბაზაში
        student=super(CollegeStudent,self).create(vals)

        last_6_number = student.personal_number[-6:]
        generated_password = f"{student.first_name.lower()}{last_6_number}"

        # 3.სისტემური მომხმარებლის შექმნა {res.users}
        user_data = {
            'name': f"{student.first_name}{student.last_name}",
            'login': student.personal_number,
            'password': generated_password,
            'email': student.email,
            'groups_id': [(4, self.env.ref('college_erp.group_college_erp_student').id),
                        (4, self.env.ref('base.group_user').id)]
            }

        new_user = self.env['res.users'].sudo().create(user_data)
        student.sudo().write({'user_id': new_user.id})
        return student

