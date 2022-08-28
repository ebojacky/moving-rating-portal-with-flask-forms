from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

API_KEY_THE_MOVIE_DB = "7f7b3dd6839b15c36b3b3b23ec32794a"


# WTFORM
class EditForm(FlaskForm):
    rating = StringField('Your Rating: /10', validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField('Save')


class AddForm(FlaskForm):
    movie_title = StringField('Enter Movie Title', validators=[DataRequired()])
    submit = SubmitField('Search')


def search_movie(title, is_id=False):
    if is_id:
        movie_search = f"https://api.themoviedb.org/3/movie/{title}?api_key={API_KEY_THE_MOVIE_DB}&language=en-US"
        response = requests.get(url=movie_search)
        response.raise_for_status()
        result = response.json()
        return {"title": result["title"],
                "year": result["release_date"][0:4],
                "description": result["overview"],
                "img_url": "https://image.tmdb.org/t/p/w500/" + result["poster_path"]
                }
    else:
        movie_search = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY_THE_MOVIE_DB}" \
                       f"&language=en-US&query={title}&page=1&include_adult=false"
        response = requests.get(url=movie_search)
        response.raise_for_status()
        results = response.json()["results"]
        return [{"title": item["title"],
                 "date": item["release_date"],
                 "online_id": item["id"]}
                for item in results]


# USING SQLALCHEMY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///top-ten-movie.db"
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)


db.create_all()

"""
# RUN this only once

new_movie = Movie(
    title="Phone Booth",
    year=2002,
    description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an "
                "extortionist's sniper rifle. Unable to leave or receive outside help, "
                "Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    rating=7.3,
    ranking=10,
    review="My favourite character was the caller.",
    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
)

db.session.add(new_movie)
db.session.commit()
"""


@app.route("/")
def home():
    # all_movies = db.session.query(Movie).all()

    all_movies = Movie.query.order_by(Movie.rating).all()
    no_of_movies = len(all_movies)
    for i in range(0, no_of_movies):
        all_movies[i].ranking = no_of_movies - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit/<movie_id>", methods=["GET", "POST"])
def edit(movie_id):
    movie = Movie.query.filter_by(id=movie_id).first()
    form = EditForm()

    if form.validate_on_submit():
        movie_to_update = Movie.query.get(movie_id)
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete/<movie_id>", methods=["GET", "POST"])
def delete(movie_id):
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()

    if form.validate_on_submit():
        movie_to_choose_from = search_movie(form.movie_title.data, False)
        return render_template("select.html", movie_options=movie_to_choose_from)

    return render_template("add.html", form=form)


@app.route("/find_details", methods=["GET", "POST"])
def find_details():
    movie_online_id = request.args.get("movie_online_id")
    movie_details = search_movie(movie_online_id, True)

    new_movie = Movie(
        title=movie_details["title"],
        year=movie_details["year"],
        description=movie_details["description"],
        rating=0,
        ranking=0,
        review="",
        img_url=movie_details["img_url"]
    )

    db.session.add(new_movie)
    db.session.commit()

    saved_movie = Movie.query.filter_by(title=movie_details["title"]).first()

    return redirect(url_for("edit", movie_id=saved_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
