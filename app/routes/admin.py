from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from app.models.user import User

admin = Blueprint('admin', __name__)

class WhitelistForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    notes = TextAreaField('Notas')
    submit = SubmitField('Añadir a la Whitelist')

@admin.route('/whitelist', methods=['GET', 'POST'])
@login_required
def manage_whitelist():
    # Solo permitir acceso a administradores - puedes ajustar esto según tu lógica de roles
    # Esta es una versión simplificada donde solo hay un administrador por nombre de usuario
    if current_user.username != 'admin':
        flash('No tienes permisos para acceder a esta página')
        return redirect(url_for('main.dashboard'))
    
    form = WhitelistForm()
    if form.validate_on_submit():
        success = User.add_email_to_whitelist(form.email.data, form.notes.data)
        if success:
            flash(f'El correo {form.email.data} ha sido añadido a la whitelist')
        else:
            flash(f'El correo {form.email.data} ya estaba en la whitelist')
        return redirect(url_for('admin.manage_whitelist'))
    
    whitelist = User.get_whitelist()
    return render_template('admin/whitelist.html', form=form, whitelist=whitelist)

@admin.route('/whitelist/delete/<email>', methods=['POST'])
@login_required
def delete_from_whitelist(email):
    # Solo permitir acceso a administradores
    if current_user.username != 'admin':
        flash('No tienes permisos para realizar esta acción')
        return redirect(url_for('main.dashboard'))
    
    success = User.remove_email_from_whitelist(email)
    if success:
        flash(f'El correo {email} ha sido eliminado de la whitelist')
    else:
        flash(f'El correo {email} no se encontró en la whitelist')
    
    return redirect(url_for('admin.manage_whitelist')) 