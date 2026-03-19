from odoo import models,fields,api

class Teacher(models.Model):
    _name="college.teacher"
    _description="College Teachers"

    name=fields.Char(string="Teacher Name",required=True)
    last_name=fields.Char(required=True)
    email=fields.Char(compute="_compute_email",readonly=True)
    user_id=fields.Many2one('res.users')
    subject_ids=fields.One2many('college.subject.selection','teachers_id')


    @api.depends('email')
    def _compute_email(self):
        for rec in self:
            rec.email=f"{rec.name}.{rec.last_name}@kolkheti.edu"

    def create(self,vals):
      teacher=super(Teacher,self).create(vals)
      generated_password=f"{teacher.name}kolkhetis_teacher"

      user_data = {
          'name': f"{teacher.name}{teacher.last_name}",
          'login': teacher.email,
          'password': generated_password,
          'email': teacher.email,
          'groups_id': [(4, self.env.ref('college_erp.group_college_erp_teacher').id),
                        (4, self.env.ref('base.group_user').id)]
      }
      new_user = self.env['res.users'].create(user_data)
      teacher.user_id=new_user
      return teacher