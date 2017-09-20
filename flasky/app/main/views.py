from flask import render_template, redirect, url_for, session, abort, flash
from . import main
from ..import db
from ..models import Role, User, Book
from .forms import EditProfileForm, EditProfileAdminForm,\
    AddBookForm, SearchForm
from flask_login import login_required, current_user
from ..decorators import admin_required, lib_required


@main.route('/', methods=['GET', 'POST'])
def index(books=[]):
    form = SearchForm()
    if form.validate_on_submit():
        bookname = form.input_.data
        session['input_data'] = bookname
        books = Book.query.filter(Book.bookname.ilike('%'+bookname+'%')).all()
        return render_template('index.html', form=form, books=books)
    return render_template('index.html', form=form, books=books)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@main.route('/book/<book_id>', methods=['GET', 'POST'])
def book(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404()
    return render_template('book_info.html', book=book)


@main.route('/del_book/<book_id>',  methods=['GET', 'POST'])
@login_required
@lib_required
def del_book(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404()
    bookname = book.bookname
    db.session.delete(book)
    flash(" the book: " + bookname + " has been deleted")
    return redirect(url_for('main.index'))


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.realname = form.realname.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.realname.data = current_user.realname
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.realname = form.realname.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.realname.data = user.realname
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/add_book', methods=['GET', 'POST'])
@login_required
@lib_required
def add_book():
    form = AddBookForm()
    if form.validate_on_submit():
        book = Book(bookname=form.bookname.data,
                    number=form.number.data,
                    subject=form.subject.data,
                    author=form.author.data,
                    ISBN=form.ISBN.data,
                    info=form.info.data,
                    publisher=form.publisher.data)
        db.session.add(book)
        flash("the book has been added")
        return redirect(url_for('main.add_book'))
    return render_template('add_book.html', form=form)
