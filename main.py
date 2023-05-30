from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask import session as session_flask
from neo4j import GraphDatabase
import random
import os
from datetime import datetime

app = Flask(__name__)

# Generate a secret key or use your own secret key
secret_key = os.urandom(24)
app.secret_key = secret_key

neo4j_uri = "neo4j+s://2144e45a.databases.neo4j.io"
neo4j_user = "neo4j"
neo4j_password = "0VbP5DwbQ2y7YcwKoGKB3vX06a8VnZiwNZp62KXyj_0"

# Inicia la conexión a Neo4j
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))


@app.route("/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Obtener los datos del formulario
        email = request.form.get("correo")
        password = request.form.get("contra")

        # Verificar si el usuario existe en la base de datos
        with driver.session() as session:
            user = session.read_transaction(_get_user_by_email, email)
            if user is None:
                return jsonify({"error": "El usuario no existe"}), 404

            # Verificar si la contraseña coincide
            if user['u']["password"] != password:
                return jsonify({"error": "La contraseña es incorrecta"}), 401

            # Store the user ID in the session
            session_flask['user_id'] = user['u']['id']

            # Verificar si es un usuario administrador
            if "admin" in user['u'].labels:
                # Página de inicio para administradores
                return render_template("admin_home.html", user=user)

            # El usuario ha iniciado sesión correctamente
            # Puedes redirigirlo a otra página o mostrar un mensaje de éxito
            return render_template("/home.html", user=user)

    # Si es una solicitud GET, mostrar la página de inicio de sesión y registro
    return render_template("/login.html")


@app.route('/logout')
def logout():
    session_flask.clear()
    return redirect(url_for('login'))


@app.route("/register", methods=["POST"])
def register():
    # Obtener los datos del formulario
    name = request.form.get("nombre_completo")
    email = request.form.get("correo")
    fecha_nac = datetime.strptime(
        request.form.get("fecha_nac"), "%Y-%m-%d").date()
    tipo_cuenta = request.form.get("tipo_cuenta")
    password = request.form.get("contrasena")

    # Variables necesarias
    id = random.randint(1, 10000000)
    cuenta_activa = True

    # Verificar si el usuario ya existe en la base de datos
    with driver.session() as session:
        user = session.read_transaction(_get_user_by_email, email)
        if user:
            return jsonify({"error": "El usuario ya existe"}), 409

        # Crear el nuevo usuario en la base de datos
        user_data = {
            "id": id,
            "name": name,
            "email": email,
            "password": password,
            "dob": fecha_nac,
            "active": cuenta_activa,
            "account_type": tipo_cuenta
        }
        session.write_transaction(_add_user, user_data)

    # El usuario se ha registrado correctamente
    # Puedes redirigirlo a otra página o mostrar un mensaje de éxito
    return render_template("/login.html")


@app.route("/login_admin", methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        # Obtener los datos del formulario
        email = request.form.get("correo")
        password = request.form.get("contra")

        # Verificar si el usuario existe en la base de datos
        with driver.session() as session:
            user = session.read_transaction(_get_user_by_email, email)
            if user is None:
                return jsonify({"error": "El usuario no existe"}), 404

            # Verificar si la contraseña coincide
            if user['u']["password"] != password:
                return jsonify({"error": "La contraseña es incorrecta"}), 401

            # Store the user ID in the session
            session_flask['user_id'] = user['u']['id']

            # Verificar si es un usuario administrador
            if "admin" in user['u'].labels:
                # Página de inicio para administradores
                return render_template("admin_home.html", user=user)

            # El usuario ha iniciado sesión correctamente
            # Puedes redirigirlo a otra página o mostrar un mensaje de éxito
            return render_template("/admin_home.html", user=user)

    # Si es una solicitud GET, mostrar la página de inicio de sesión y registro
    return render_template("/login_admin.html")


@app.route("/register_admin", methods=["POST"])
def register_admin():
    # Obtener los datos del formulario
    name = request.form.get("nombre_completo")
    email = request.form.get("correo")
    fecha_nac = datetime.strptime(
        request.form.get("fecha_nac"), "%Y-%m-%d").date()
    password = request.form.get("contrasena")

    # Variables necesarias
    id = random.randint(1, 10000000)
    cuenta_activa = True

    # Verificar si el usuario ya existe en la base de datos
    with driver.session() as session:
        user = session.read_transaction(_get_user_by_email, email)
        if user:
            return jsonify({"error": "El usuario ya existe"}), 409

        # Crear el nuevo usuario en la base de datos
        admin_data = {
            "id": id,
            "name": name,
            "email": email,
            "password": password,
            "dob": fecha_nac,
            "active": cuenta_activa,
        }
        session.write_transaction(_add_admin, admin_data)

    # El usuario se ha registrado correctamente
    # Puedes redirigirlo a otra página o mostrar un mensaje de éxito
    return render_template("/login_admin.html")


@app.route("/admin_home", methods=['GET'])
def admin_home():
    # Get the user ID from the session
    user_id = session_flask.get('user_id')

    with driver.session() as session:
        # Query the user by ID
        user = session.read_transaction(_get_user_by_id, user_id)

    # Check if the user is logged in
    if user is None:
        return redirect(url_for('login_admin'))

    return render_template("/admin_home.html", user=user)

# Funciones de edición de contenido


@app.route("/add_content", methods=["GET", "POST"])
def add_content():
    # Get the user ID from the session
    user_id = session_flask.get('user_id')

    with driver.session() as session:
        # Query the user by ID
        user = session.read_transaction(_get_user_by_id, user_id)

    # Check if the user is logged in
    if user is None:
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        # Obtener los datos del formulario
        content_type = request.form.get("content_type")
        title = request.form.get("title")
        release_date = request.form.get("release_date")
        genre = request.form.get("genre")
        duration = request.form.get("duration")
        image = request.form.get("image")

        genre_list = genre.split(",")

        if content_type == "movie":
            # Variables necesarias para una película
            id = random.randint(1, 10000000)

            # Crear la nueva película en la base de datos
            movie_data = {
                "id": id,
                "title": title,
                "release_date": release_date,
                "genre": genre_list,
                "duration": duration,
                "image": image
            }
            with driver.session() as session:
                session.write_transaction(_add_movie, movie_data)

        elif content_type == "series":
            # Variables necesarias para una serie
            id = random.randint(1, 10000000)
            episode_duration = request.form.get("episode_duration")
            total_episodes = request.form.get("total_episodes")

            # Crear la nueva serie en la base de datos
            series_data = {
                "id": id,
                "title": title,
                "release_date": release_date,
                "genre": genre_list,
                "episode_duration": episode_duration,
                "total_episodes": total_episodes
            }
            with driver.session() as session:
                session.write_transaction(_add_series, series_data)

    return render_template("/agregar_contenido.html", user=user)


@app.route("/edit_content/<content_id>", methods=["GET", "POST"])
def edit_content(content_id):
    # Obtener el usuario actual de la sesión
    user = session.get("user")
    if not user or "admin" not in user["u"].labels:
        return redirect(url_for("login_admin"))

    # Obtener los detalles del contenido por su ID
    with driver.session() as session:
        content = session.read_transaction(_get_content_by_id, content_id)
        if not content:
            return jsonify({"error": "El contenido no existe"}), 404

        if request.method == "POST":
            # Actualizar los datos del contenido
            content_type = request.form.get("content_type")
            title = request.form.get("title")
            release_date = request.form.get("release_date")
            genre = request.form.get("genre")
            duration = request.form.get("duration")
            image = request.form.get("image")

            if content_type == "movie":
                # Actualizar la película en la base de datos
                movie_data = {
                    "id": content_id,
                    "title": title,
                    "release_date": release_date,
                    "genre": genre,
                    "duration": duration,
                    "image": image
                }
                session.write_transaction(_update_movie, movie_data)

            elif content_type == "series":
                # Actualizar la serie en la base de datos
                episode_duration = request.form.get("episode_duration")
                total_episodes = request.form.get("total_episodes")
                series_data = {
                    "id": content_id,
                    "title": title,
                    "release_date": release_date,
                    "genre": genre,
                    "episode_duration": episode_duration,
                    "total_episodes": total_episodes
                }
                session.write_transaction(_update_series, series_data)

            return redirect(url_for("admin_dashboard"))

    return render_template("edit_content.html", user=user, content=content)


@app.route("/delete_content/<content_id>", methods=["POST"])
def delete_content(content_id):
    # Obtener el usuario actual de la sesión
    user = session.get("user")
    if not user or "admin" not in user["u"].labels:
        return redirect(url_for("login_admin"))

    # Eliminar el contenido de la base de datos
    with driver.session() as session:
        session.write_transaction(_delete_content, content_id)

    return redirect(url_for("admin_dashboard"))


@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_add_user, data)
    return jsonify({"message": "User created successfully"}), 201


def _add_user(tx, data):
    tx.run(
        "CREATE (u:User:Customer {id: $id, name: $name, email: $email, password: $password, dob: $dob, active: $active, account_type: $account_type})",
        id=data.get("id"),
        name=data.get("name"),
        email=data.get("email"),
        password=data.get("password"),
        dob=data.get("dob"),
        active=data.get("active"),
        account_type=data.get("account_type"),
    )


@app.route("/add_admin", methods=["POST"])
def add_admin():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_add_admin, data)
    return jsonify({"message": "Admin created successfully"}), 201


def _add_admin(tx, data):
    tx.run(
        "CREATE (a:User:Admin {id: $id, name: $name, email: $email, password: $password, dob: $dob, active: $active})",
        id=data.get("id"),
        name=data.get("name"),
        email=data.get("email"),
        password=data.get("password"),
        dob=data.get("dob"),
        active=data.get("active"),
    )


@app.route("/add_movie", methods=["POST"])
def add_movie():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_add_movie, data)
    return jsonify({"message": "Movie created successfully"}), 201


def _add_movie(tx, data):
    tx.run(
        "CREATE (m:Content:Movie {id: $id, title: $title, release_date: $release_date, genre: $genre, duration: $duration, image: $image})",
        id=data.get("id"),
        title=data.get("title"),
        release_date=data.get("release_date"),
        genre=data.get("genre"),
        duration=data.get("duration"),
        image=data.get("image"),
    )


@app.route("/add_series", methods=["POST"])
def add_series():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_add_series, data)
    return jsonify({"message": "Series created successfully"}), 201


def _add_series(tx, data):
    tx.run(
        "CREATE (s:Content:Series {id: $id, title: $title, release_date: $release_date, genre: $genre, episode_duration: $episode_duration, total_episodes: $total_episodes})",
        id=data.get("id"),
        title=data.get("title"),
        release_date=data.get("release_date"),
        genre=data.get("genre"),
        episode_duration=data.get("episode_duration"),
        total_episodes=data.get("total_episodes"),
    )


@app.route("/add_actor", methods=["POST"])
def add_actor():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_add_actor, data)
    return jsonify({"message": "Actor created successfully"}), 201


def _add_actor(tx, data):
    tx.run(
        "CREATE (a:Staff:Actor {id: $id, name: $name, dob: $dob, nationality: $nationality, awards: $awards, role: $role})",
        id=data.get("id"),
        name=data.get("name"),
        dob=data.get("dob"),
        nationality=data.get("nationality"),
        awards=data.get("awards"),
        role=data.get("role"),
    )


@app.route("/add_director", methods=["POST"])
def add_director():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_add_director, data)
    return jsonify({"message": "Director created successfully"}), 201


def _add_director(tx, data):
    tx.run(
        "CREATE (d:Staff:Director {id: $id, name: $name, dob: $dob, nationality: $nationality})",
        id=data.get("id"),
        name=data.get("name"),
        dob=data.get("dob"),
        nationality=data.get("nationality"),
    )


@app.route("/create_view_relation", methods=["POST"])
def create_view_relation():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_create_view_relation, data)
    return jsonify({"message": "View relation created successfully"}), 201


def _create_view_relation(tx, data):
    query = """
    MATCH (u:User {id: $user_id})
    MATCH (c:Content {id: $content_id})
    CREATE (u)-[v:Viewed {date: $date, rating: $rating, review: $review, watchlist: $watchlist}]->(c)
    """
    tx.run(
        query,
        user_id=data.get("user_id"),
        content_id=data.get("content_id"),
        date=data.get("date"),
        rating=data.get("rating"),
        review=data.get("review"),
        watchlist=data.get("watchlist"),
    )


@app.route("/create_recommended_relation", methods=["POST"])
def create_recommended_relation():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_create_recommended_relation, data)
    return jsonify({"message": "Recommended relation created successfully"}), 201


def _create_recommended_relation(tx, data):
    query = """
    MATCH (u:User {id: $user_id})
    MATCH (c:Content {id: $content_id})
    CREATE (u)-[r:Recommended {recommendation_date: $recommendation_date, recommendation_score: $recommendation_score, watched: $watched}]->(c)
    """
    tx.run(
        query,
        user_id=data.get("user_id"),
        content_id=data.get("content_id"),
        recommendation_date=data.get("recommendation_date"),
        recommendation_score=data.get("recommendation_score"),
        watched=data.get("watched"),
    )


@app.route("/create_acted_in_relation", methods=["POST"])
def create_acted_in_relation():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_create_acted_in_relation, data)
    return jsonify({"message": "Acted_In relation created successfully"}), 201


def _create_acted_in_relation(tx, data):
    query = """
    MATCH (c:Content {id: $content_id})
    MATCH (a:Staff:Actor {id: $actor_id})
    CREATE (c)-[r:Acted_By {character: $character, hiring_date: $hiring_date, salary: $salary}]->(a)
    """
    tx.run(
        query,
        content_id=data.get("content_id"),
        actor_id=data.get("actor_id"),
        character=data.get("character"),
        hiring_date=data.get("hiring_date"),
        salary=data.get("salary"),
    )


@app.route("/create_directed_by_relation", methods=["POST"])
def create_directed_by_relation():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_create_directed_by_relation, data)
    return jsonify({"message": "Directed_By relation created successfully"}), 201


def _create_directed_by_relation(tx, data):
    query = """
    MATCH (c:Content {id: $content_id})
    MATCH (d:Staff:Director {id: $director_id})
    CREATE (c)-[r:Directed_By {hiring_date: $hiring_date, salary: $salary}]->(d)
    """
    tx.run(
        query,
        content_id=data.get("content_id"),
        director_id=data.get("director_id"),
        hiring_date=data.get("hiring_date"),
        salary=data.get("salary"),
    )

# Función para obtener un usuario por su correo electrónico


def _get_user_by_email(tx, email):
    query = "MATCH (u:User) WHERE u.email = $email RETURN u"
    result = tx.run(query, email=email)
    return result.single()


def _get_user_by_id(tx, id):
    query = "MATCH (u:User) WHERE u.id = $id RETURN u"
    result = tx.run(query, id=id)
    return result.single()


def _get_content_by_id(tx, content_id):
    result = tx.run(
        """
        MATCH (c) WHERE c.id = $content_id RETURN c
        """,
        content_id=content_id
    )
    return result.single()


def _update_movie(tx, movie_data):
    tx.run(
        """
        MATCH (m:Movie {id: $id})
        SET m.title = $title, m.release_date = $release_date, m.genre = $genre, m.duration = $duration, m.image = $image
        """,
        **movie_data
    )


def _update_series(tx, series_data):
    tx.run(
        """
        MATCH (s:Series {id: $id})
        SET s.title = $title, s.release_date = $release_date, s.genre = $genre, s.episode_duration = $episode_duration, s.total_episodes = $total_episodes
        """,
        **series_data
    )


def _delete_content(tx, content_id):
    tx.run(
        """
        MATCH (c) WHERE c.id = $content_id DELETE c
        """,
        content_id=content_id
    )


if __name__ == "__main__":
    app.run(debug=True)
