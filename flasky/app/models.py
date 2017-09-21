from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
from datetime import datetime, timedelta


class Permission:
    SEARCH = 0x01
    BORROW_BOOK = 0X02
    RETURN_BOOK = 0x04
    ADD_BOOK = 0x08
    DELETE_BOOK = 0X10
    MODIFY_BOOK = 0X20
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'Reader': (Permission.SEARCH |
                       Permission.BORROW_BOOK |
                       Permission.RETURN_BOOK, True),
            'Librarian': (Permission.SEARCH |
                          Permission.ADD_BOOK |
                          Permission.BORROW_BOOK |
                          Permission.RETURN_BOOK |
                          Permission.DELETE_BOOK |
                          Permission.MODIFY_BOOK, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    realname = db.Column(db.String(64))
    confirmed = db.Column(db.Boolean, default=False) # 账号是否已经确认过
    borrowed_number = db.Column(db.Integer, default=0) # 已借的书籍数量
    # backref属性反向关联使得record可以直接通过user属性获取相应的user对象
    Records = db.relationship('Record', backref=db.backref('user', lazy='joined'),
                                        lazy='dynamic',
                                        cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def can_borrow(self):
        records = self.Records
        for record in records:
            if(record.returned is False and (datetime.now() > record.end_time)):
                return False
        if(self.confirmed and self.borrowed_number <= 5):
            return True
        else:
            return False

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_lib(self):
        return self.can(Permission.ADD_BOOK)

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def is_lib(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    bookname = db.Column(db.String(128), index=True)
    info = db.Column(db.Text())
    author = db.Column(db.String(128))
    totalNumber = db.Column(db.Integer, default=0)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    publisher = db.Column(db.String(256))
    ISBN = db.Column(db.String(128))
    location = db.Column(db.String(128))
    # 反向关系给Book_entities添加book属性, book_entities可以直接获取相应Book对象
    book_entities = db.relationship('Book_entity', backref=db.backref('book', lazy='joined'),
                                        lazy='dynamic',
                                        cascade='all, delete-orphan')


class Record(db.Model):
    __tablename__ = "records"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    sequence = db.Column(db.Integer, db.ForeignKey('book_entities.sequence'), primary_key=True)
    borrow_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime)
    returned = db.Column(db.Boolean, default=False)
    book_id = db.Column(db.Integer)


class Book_entity(db.Model):
    __tablename__ = "book_entities"
    sequence = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    confirmed = db.Column(db.Boolean, default=True)
    # 反向关系给Record添加book_entity属性,Record可以直接获取相应book_entity对象
    Records = db.relationship('Record', backref=db.backref('book_entity', lazy='joined'),
                                        lazy='dynamic',
                                        cascade='all, delete-orphan')

    def can_borrow(self):
        if(self.confirmed):
            return True
        else:
            return False

    def create_record(self, book_id, user_id):
        borrow_time = datetime.now()
        end_time = datetime.now() + timedelta(days=15)
        record = Record(sequence=self.sequence, user_id=user_id,
                        book_id=book_id, borrow_time=borrow_time,
                        end_time=end_time)
        db.session.add(record)


class subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    subjectname = db.Column(db.String(64))
    books = db.relationship('Book', backref=db.backref('subject', lazy="joined"),
                                                        lazy='dynamic', 
                                                        cascade="all, delete-orphan")
