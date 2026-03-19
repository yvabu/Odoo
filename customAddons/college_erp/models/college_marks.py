from email.policy import default
from odoo.exceptions import ValidationError
from odoo import models,fields,api
from odoo.odoo.api import readonly


class CollegeMark(models.Model):
    _name = 'college.mark'
    _description = 'Student Marks'
    _rec_name="student_id"

    student_id = fields.Many2one('college.student', required=True)
    subject_id = fields.Many2one('college.subjects', required=True)
    teacher_id=fields.Many2one('college.teacher',compute="_compute_teacher",store=True,readonly=True)
    comment = fields.Text(string="მასწავლებლის კომენტარი")

    #ვწერ კვირის ქულებს
    w1=fields.Float(string="კვირა 1",default=0)
    w2=fields.Float(string="კვირა 2",default=0)
    w3=fields.Float(string="კვირა 3",default=0)
    w4=fields.Float(string="კვირა 4",default=0)
    w5=fields.Float(string="კვირა 5",default=0)
    w6=fields.Float(string="კვირა 6",default=0)
    w7=fields.Float(string="კვირა 7",default=0)
    w8=fields.Float(string="კვირა 8",default=0)
    w9=fields.Float(string="კვირა 9",default=0)
    w10=fields.Float(string="კვირა 10",default=0)

    shualeduri=fields.Float(string="შუალედური გამოცდის შეფასება")
    final=fields.Float(string="ფინალური გამოცდის შეფასება")
    total_marks=fields.Float(string="საბოლოო შეფასება",compute="_compute_total_marks")


    @api.depends('student_id','subject_id')
    def _compute_teacher(self):
        for rec in self:
            if rec.student_id and rec.subject_id:
                if rec.student_id in rec.subject_id.student_ids:
                    rec.teacher_id=rec.subject_id.teacher_id
                else:
                    rec.teacher_id=False
            else:
                rec.teacher_id=False
    @api.depends('w1','w2','w3','w4','w5','w6','w7','w8','w9','w10','shualeduri','final')
    def _compute_total_marks(self):
        for rec in self:
            rec.total_marks=sum([rec.w1,rec.w2,rec.w3,rec.w4,rec.w5,rec.w6,rec.w7,rec.w8,rec.w9,rec.w10,rec.shualeduri,rec.final])

    @api.constrains('w1','w2','w3','w4','w5','w6','w7','w8','w9','w10','shualeduri','final')
    def _check_marks(self):
        for rec in self:
            weeks=[rec.w1,rec.w2,rec.w3,rec.w4,rec.w5,rec.w6,rec.w7,rec.w8,rec.w9,rec.w10]
            for w in weeks:
                if w>3 or w<0:
                    raise ValidationError("კვირის ქულა უნდა იყოს 0-დან 3-მდე!")

            if rec.shualeduri > 30 or rec.shualeduri <0:
                raise ValidationError("შუალედურის ქულა უნდა იყოს 0-დან 30-მდე!")
            if rec.final>40 or rec.final <0:
                raise ValidationError("ფინალურის ქულა უნდა იყოს 0-დან 40-მდე!")

