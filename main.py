from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from wtforms import StringField, SubmitField, HiddenField
from secrets import token_hex
from datetime import datetime, date


app = Flask(__name__)
app.config['SECRET_KEY'] = '233123dads^$%^$%Twfwfr34b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///magic_events_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    submit = SubmitField('Reserve attendance at this event now')

    def to_dict(self):
        return {
                'name': self.name.data,
                'email': self.email.data,
                'phone': self.phone.data
                }


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    img_thumbnail = db.Column(db.String(500), nullable=False)
    reservations = db.relationship('Reservation', backref='event')


class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    code = db.Column(db.String(500), unique=True, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))


@app.route('/')
def index():
    return render_template('index.html', events=Event.query.all())


@app.route('/register', methods=['GET', 'POST'])
def register():
    event_id = request.args.get('event_id')
    event = Event.query.get(event_id)
    if not event:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        code = token_hex(10)
        reservation = Reservation(**form.to_dict(), code=code, date=datetime.now())
        event.reservations.append(reservation)
        db.session.add(event)
        db.session.add(reservation)
        db.session.commit()
        return render_template('registration_successful.html', event=event, code=code)
    return render_template('register.html', form=form)


@app.route('/insert-code')
def insert_code():
    message = ''
    if request.args.get('bad_code'):
        message = "You've entered wrong management code. Maybe a typo?"
    return render_template('code.html', message=message)


@app.route('/manage')
def manage():
    code = request.args.get('code')
    reservation = Reservation.query.filter_by(code=code).first()
    if not reservation:
        return redirect(url_for('insert_code', bad_code=True))
    event = Event.query.get(reservation.event_id)
    can_cancel = True
    message = ''
    days_passed_since_booked = reservation.date.date() - date.today()

    if abs(days_passed_since_booked.days) >= 3:
        can_cancel = False
        message = "You can't cancel a booking that lasts longer than two days"

    days_left_to_event = event.start.date() - date.today()
    if days_left_to_event.days <= 2:
        can_cancel = False
        message = "You can't cancel a booking later than two days before the start date of the event"

    return render_template('manage.html',
                           reservation=reservation,
                           event=event,
                           can_cancel=can_cancel,
                           message=message
                           )


@app.route('/delete')
def delete():
    reservation_id = request.args.get('id_')
    code = request.args.get('code')
    reservation_to_delete = Reservation.query.get(reservation_id)

    if reservation_to_delete.code == code:
        db.session.delete(reservation_to_delete)
        db.session.commit()
        return render_template('deleted.html')
    return redirect(url_for('/'))


if __name__ == '__main__':
    app.run(debug=True)
