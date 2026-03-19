from odoo import fields,models,api

class ForStudent(models.Model):
    _name="for.student"
    _description= "For Student"
    _rec_name="user_id"

    student_id = fields.Many2one('college.student',string="Student",required=True)
    user_id=fields.Many2one('res.users',string="User",readonly=False,related='student_id.user_id', store=True)
    subject_ids = fields.Many2many('college.subjects', string="Subjects")
    mark_ids = fields.One2many('college.mark','student_id',related='student_id.mark_ids',string="შეფასებები")
    student_pers_num=fields.Char(related="student_id.personal_number",readonly=True,string="ჩემი პირადი ნომერი")
    student_img=fields.Image(related="student_id.image_1920",readonly=True,string="სტუდენთის ფოტო")
    student_email=fields.Char(related="student_id.email",readonly=True,string="ჩემი ემაილი")
    @api.onchange('user_id')
    def _onchange_user(self):
        student=self.env['college.student'].search([('user_id','=',self.user_id.id)],limit=1)
        if student:
            self.student_id=student.id
            self.subject_ids=student.subject_ids