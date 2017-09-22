from flask import render_template, redirect, url_for, session, abort, flash
from . import main
from ..import db
from ..models import Role, User, Book, Book_entity
from .forms import EditProfileForm, EditProfileAdminForm,\
    AddBookForm, SearchForm, EditBookForm, BorrowForm, ReturnForm
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
    # 此处可以增加用户借书记录查看
    records = user.Records
    return render_template('user.html', user=user, records=records)


@main.route('/book/<book_id>', methods=['GET', 'POST'])
def book(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404()
    book_entities = book.book_entities.all()
    nowNumber = 0
    for book_entity in book_entities:
        if(book_entity.confirmed):
            nowNumber += 1
    return render_template('book_info.html', book=book, nowNumber=nowNumber)


@main.route('/del_book/<book_id>',  methods=['GET', 'POST'])
@login_required
@lib_required
def del_book(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404()
    bookname = book.bookname
    db.session.delete(book)
    flash(" the book: " + bookname + " has been deleted")
    return redirect(url_for('main.index'))


@main.route('/edit_book/<book_id>', methods=['GET', 'POST'])
@login_required
@lib_required
def edit_book(book_id):
    book = Book.query.filter_by(id=book_id).first_or_404()
    form = EditBookForm()
    oldname = book.bookname
    if form.validate_on_submit():
        book.bookname = form.bookname.data
        book.info = form.info.data
        book.author = form.author.data
        book.publisher = form.publisher.data
        book.subject_id = form.subject_id.data
        book.location = form.location.data
        book.ISBN = form.ISBN.data
        db.session.add(book)
        flash("the book: <"+oldname+"> has been modified ")
        return redirect(url_for('main.book', book_id=book.id))
    form.bookname.data = book.bookname
    form.info.data = book.info
    form.author.data = book.author
    form.publisher.data = book.publisher
    form.subject_id.data = book.subject_id
    form.location.data = book.location
    form.ISBN.data = book.ISBN
    return render_template('edit_book.html', form=form, book=book)


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
                    totalNumber=form.totalnumber.data,
                    subject_id=form.subject_id.data,
                    author=form.author.data,
                    ISBN=form.ISBN.data,
                    info=form.info.data,
                    publisher=form.publisher.data,
                    location=form.location.data)
        db.session.add(book)
        db.session.commit()
        for i in range(book.totalNumber):
            book_entity = Book_entity(book_id=book.id)
            db.session.add(book_entity)
        flash("the book has been added")
        return redirect(url_for('main.add_book'))
    return render_template('add_book.html', form=form)


@main.route('/borrow_book', methods=['GET', 'POST'])
@login_required
@lib_required
def borrow_book():
    form = BorrowForm()
    if form.validate_on_submit():
        sequenceNumber = form.sequence.data
        bookCopy = Book_entity.query.get_or_404(sequenceNumber)
        book_id = bookCopy.book_id
        user_id = form.user_id.data
        if(bookCopy.can_borrow()):
            user = User.query.get_or_404(user_id)
            if(user.can_borrow()):
                bookCopy.confirmed = False
                user.borrowed_number += 1
                bookCopy.create_record(book_id, user_id)
                db.session.add(user)
                db.session.add(bookCopy)
                flash("borrow successfully")
                return redirect(url_for('main.borrow_book'))
            else:
                flash('''the person can't borrow book''')
                return redirect(url_for('main.borrow_book'))
        else:
            flash("the book hasn't been returned")
            return redirect(url_for('main.borrow_book'))
    return render_template('borrow_book.html', form=form)


@main.route('/return_book', methods=['GET', 'POST'])
@login_required
@lib_required
def return_book():
    form = ReturnForm()
    if form.validate_on_submit():
        sequenceNumber = form.sequence.data
        bookReturned = Book_entity.query.get_or_404(sequenceNumber)
        if(bookReturned.can_return()):
            if(bookReturned.book_return()):
                flash("return book successful")
                return redirect(url_for('main.return_book'))
            else:
                flash("return book failed")
                return redirect(url_for('main.return_book'))
        else:
            flash("the book is already returned")
            return redirect(url_for('main.return_book'))
    else:
        return render_template('return_book.html', form=form)
