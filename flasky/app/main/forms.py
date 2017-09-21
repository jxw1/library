from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField,\
    TextAreaField, IntegerField
from wtforms.validators import Required, Length, Email, Regexp
from ..models import Role, User, Book, Record
from wtforms import ValidationError


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    realname = StringField('Real name', validators=[Length(0, 64)])
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    realname = StringField('real name', validators=[Length(0, 64)])
    submit = SubmitField('submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                    User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already in use")


class AddBookForm(FlaskForm):
    bookname = StringField('book name', validators=[Required()])
    info = TextAreaField('book info', validators=[Required()])
    author = StringField('author name', validators=[Required()])
    totalnumber = IntegerField('the totalnumber of book', validators=[Required()])
    subject_id = IntegerField('the subject_id of book')
    ISBN = StringField('ISBN', validators=[Required()])
    publisher = StringField('publisher', validators=[Required()])
    location = StringField('the location of the book', validators=[Required()])
    submit = SubmitField('submit')

    def validate_ISBN(self, field):
        if Book.query.filter_by(ISBN=field.data).first():
            raise ValidationError('the book already existed.')


class EditBookForm(FlaskForm):
    bookname = StringField('book name', validators=[Required()])
    info = TextAreaField('book info', validators=[Required()])
    author = StringField('author name', validators=[Required()])
    subject_id = IntegerField('the subject_id of book')
    ISBN = StringField('ISBN', validators=[Required()])
    publisher = StringField('publisher', validators=[Required()])
    location = StringField('the location of the book', validators=[Required()])
    submit = SubmitField('submit')


class SearchForm(FlaskForm):
    # choices = [('bookname')]
    # type = SelectField
    input_ = StringField('book name', validators=[Required()])
    submit = SubmitField('search book')


class BorrowForm(FlaskForm):
    sequence = IntegerField('the sequence number of the book', validators=[Required()])
    book_id = IntegerField('the book_id of book', validators=[Required()])
    user_id = IntegerField('the id of the borrower', validators=[Required()])
    submit = SubmitField('submit')
