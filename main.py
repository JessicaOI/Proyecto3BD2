from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    flash,
    session,
)
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


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Obtener los datos del formulario
        email = request.form.get("correo")
        password = request.form.get("contra")

        # Verificar si el usuario existe en la base de datos
        with driver.session() as session:
            user = session.read_transaction(_get_user_by_email, email)
            if user is None:
                return jsonify({"error": "El usuario no existe"}), 404

            # Verificar si la contraseña coincide
            if user["u"]["password"] != password:
                return jsonify({"error": "La contraseña es incorrecta"}), 401

            # Get all content from the database
            contents = session.read_transaction(_get_all_content)

            # Store the user ID in the session
            session_flask["user_id"] = user["u"]["id"]

            # Verificar si es un usuario administrador
            if "admin" in user["u"].labels:
                # Página de inicio para administradores
                return redirect(url_for("admin_home"))

            # El usuario ha iniciado sesión correctamente
            # Redirigir a la página de películas
            return redirect(url_for("movies"))

    # Si es una solicitud GET, mostrar la página de inicio de sesión y registro
    return render_template("/login.html")


@app.route("/logout")
def logout():
    session_flask.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["POST"])
def register():
    # Obtener los datos del formulario
    name = request.form.get("nombre_completo")
    email = request.form.get("correo")
    fecha_nac = datetime.strptime(request.form.get("fecha_nac"), "%Y-%m-%d").date()
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
            "account_type": tipo_cuenta,
        }
        session.write_transaction(_add_user, user_data)

    # El usuario se ha registrado correctamente
    # Puedes redirigirlo a otra página o mostrar un mensaje de éxito
    return render_template("/login.html")


@app.route("/login_admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        # Obtener los datos del formulario
        email = request.form.get("correo")
        password = request.form.get("contra")

        # Verificar si el usuario existe en la base de datos
        with driver.session() as session:
            user = session.read_transaction(_get_user_by_email, email)
            if user is None:
                return jsonify({"error": "El usuario no existe"}), 404

            # Verificar si la contraseña coincide
            if user["u"]["password"] != password:
                return jsonify({"error": "La contraseña es incorrecta"}), 401

            # Get all content from the database
            contents = session.read_transaction(_get_all_content)

            # Store the user ID in the session
            session_flask["user_id"] = user["u"]["id"]

            # Verificar si es un usuario administrador
            if "admin" in user["u"].labels:
                # Página de inicio para administradores
                return redirect(url_for("admin_home"))

            # El usuario ha iniciado sesión correctamente
            # Puedes redirigirlo a otra página o mostrar un mensaje de éxito
            return redirect(url_for("admin_home"))

    # Si es una solicitud GET, mostrar la página de inicio de sesión y registro
    return render_template("/login_admin.html")


@app.route("/register_admin", methods=["POST"])
def register_admin():
    # Obtener los datos del formulario
    name = request.form.get("nombre_completo")
    email = request.form.get("correo")
    fecha_nac = datetime.strptime(request.form.get("fecha_nac"), "%Y-%m-%d").date()
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


@app.route("/admin_home", methods=["GET"])
def admin_home():
    # Get the user ID from the session
    user_id = session_flask.get("user_id")

    with driver.session() as session:
        # Query the user by ID
        user = session.read_transaction(_get_user_by_id, user_id)

        # Check if the user is logged in
        if user is None:
            return redirect(url_for("admin_home"))

        # Get all content from the database
        contents = session.read_transaction(_get_all_content)

    return render_template("/admin_home.html", user=user, contents=contents)


# Funciones de edición de contenido


@app.route("/add_content", methods=["GET", "POST"])
def add_content():
    # Get the user ID from the session
    user_id = session_flask.get("user_id")

    with driver.session() as session:
        # Query the user by ID
        user = session.read_transaction(_get_user_by_id, user_id)

    # Check if the user is logged in
    if user is None:
        return redirect(url_for("login_admin"))

    if "message" in session_flask:
        flash(session_flask["message"])
        session_flask.pop("message", None)

    if request.method == "POST":
        # Obtener los datos del formulario
        content_type = request.form.get("content_type")
        title = request.form.get("title")
        release_date = datetime.strptime(
            request.form.get("release_date"), "%Y-%m-%d"
        ).date()
        genre = request.form.get("genre")
        duration = int(request.form.get("duration"))
        image = request.form.get("image")
        nota = request.form.get("nota")

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
                "image": image,
            }
            with driver.session() as session:
                session.write_transaction(_add_movie, movie_data)

            backlog = (
                f"Backlog: Pelicula {title} creada por el usuario {user['u']['name']}"
            )

            # Crear relación entre el administrador y el contenido creado
            relation_data = {
                "admin_id": user_id,
                "content_id": id,
                "fecha_de_adicion": datetime.today().date(),  # Fecha actual
                "nota": nota,  # Aquí puedes guardar una nota si es necesario
                "backlog": backlog,  # Aquí puedes guardar información sobre el backlog si es necesario
            }
            with driver.session() as session:
                session.write_transaction(_create_content_relation, relation_data)

            flash("Contenido creado con éxito")

        elif content_type == "series":
            # Variables necesarias para una serie
            id = random.randint(1, 10000000)
            total_episodes = int(request.form.get("total_episodes"))

            # Crear la nueva serie en la base de datos
            series_data = {
                "id": id,
                "title": title,
                "release_date": release_date,
                "genre": genre_list,
                "episode_duration": duration,
                "total_episodes": total_episodes,
                "image": image,
            }
            with driver.session() as session:
                session.write_transaction(_add_series, series_data)

            backlog = (
                f"Backlog: Serie {title} creada por el usuario {user['u']['name']}"
            )

            # Crear relación entre el administrador y el contenido creado
            relation_data = {
                "admin_id": user_id,
                "content_id": id,
                "fecha_de_adicion": datetime.today().date(),  # Fecha actual
                "nota": nota,  # Aquí puedes guardar una nota si es necesario
                "backlog": backlog,  # Aquí puedes guardar información sobre el backlog si es necesario
            }
            with driver.session() as session:
                session.write_transaction(_create_content_relation, relation_data)

            flash("Contenido creado con éxito")

    return render_template("/agregar_contenido.html", user=user)


@app.route("/edit_content/<content_id>", methods=["GET", "POST"])
def edit_content(content_id):
    # Get the user ID from the session
    user_id = session_flask.get("user_id")

    with driver.session() as session:
        # Query the user by ID
        user = session.read_transaction(_get_user_by_id, user_id)
        content = session.read_transaction(_get_content_by_id, content_id)

    # Check if the user is logged in
    if user is None:
        return redirect(url_for("login_admin"))

    if "message" in session_flask:
        flash(session_flask["message"])
        session_flask.pop("message", None)

    if request.method == "POST":
        # Obtener los datos del formulario
        content_type = request.form.get("content_type")
        title = request.form.get("title")
        release_date = datetime.strptime(
            request.form.get("release_date"), "%Y-%m-%d"
        ).date()
        genre = request.form.get("genre")
        duration = request.form.get("duration")
        image = request.form.get("image")
        nota = request.form.get("nota")

        genre_list = genre.split(",")

        if content_type == "movie":

            # Crear la nueva película en la base de datos
            movie_data = {
                "id": content_id,
                "title": title,
                "release_date": release_date,
                "genre": genre_list,
                "duration": duration,
                "image": image,
            }
            with driver.session() as session:
                session.write_transaction(_update_movie, movie_data)

            backlog = (
                f"Backlog: Pelicula {title} creada por el usuario {user['u']['name']}"
            )

            # Crear relación entre el administrador y el contenido creado
            relation_data = {
                "admin_id": user_id,
                "content_id": content_id,
                "fecha_de_adicion": datetime.today().date(),  # Fecha actual
                "nota": nota,  # Aquí puedes guardar una nota si es necesario
                "backlog": backlog,  # Aquí puedes guardar información sobre el backlog si es necesario
            }
            with driver.session() as session:
                session.write_transaction(_edit_content_relation, relation_data)

            flash("Contenido editado con éxito")

        elif content_type == "series":
            total_episodes = request.form.get("total_episodes")

            # Crear la nueva serie en la base de datos
            series_data = {
                "id": content_id,
                "title": title,
                "release_date": release_date,
                "genre": genre_list,
                "episode_duration": duration,
                "total_episodes": total_episodes,
            }
            with driver.session() as session:
                session.write_transaction(_update_series, series_data)

            backlog = (
                f"Backlog: Serie {title} creada por el usuario {user['u']['name']}"
            )

            # Crear relación entre el administrador y el contenido creado
            relation_data = {
                "admin_id": user_id,
                "content_id": content_id,
                "fecha_de_adicion": datetime.today().date(),  # Fecha actual
                "nota": nota,  # Aquí puedes guardar una nota si es necesario
                "backlog": backlog,  # Aquí puedes guardar información sobre el backlog si es necesario
            }
            with driver.session() as session:
                session.write_transaction(_edit_content_relation, relation_data)

            flash("Contenido editado con éxito")

    return render_template(
        "/editar_contenido.html", user=user, content=content, content_id=content_id
    )


@app.route("/delete_content/<content_id>", methods=["POST"])
def delete_content(content_id):
    with driver.session() as session:
        session.write_transaction(_delete_content, content_id)
    flash("Contenido eliminado con éxito")
    return redirect(url_for("admin_home"))


# Añadir Actores


@app.route("/add_actor/<content_id>", methods=["GET", "POST"])
def add_actor(content_id):
    # Get the user ID from the session
    user_id = session_flask.get("user_id")

    with driver.session() as session:
        # Query the user by ID
        user = session.read_transaction(_get_user_by_id, user_id)

    # Check if the user is logged in
    if user is None:
        return redirect(url_for("login_admin"))

    if "message" in session_flask:
        flash(session_flask["message"])
        session_flask.pop("message", None)

    if request.method == "POST":
        # Obtener los datos del formulario
        name = request.form.get("name")
        dob = datetime.strptime(request.form.get("dob"), "%Y-%m-%d").date()
        nacionality = request.form.get("nacionality")
        awards = request.form.get("awards")
        role = request.form.get("role")
        hiring_date = datetime.strptime(
            request.form.get("hiring_date"), "%Y-%m-%d"
        ).date()
        salary = int(request.form.get("salary"))
        character = request.form.get("character")

        id = random.randint(1, 10000000)

        # Crear la nueva película en la base de datos
        actor_data = {
            "id": id,
            "name": name,
            "nacionality": nacionality,
            "dob": dob,
            "awards": awards,
            "role": role,
        }
        with driver.session() as session:
            session.write_transaction(_add_actor, actor_data)

        relation_data = {
            "content_id": content_id,
            "actor_id": id,
            "hiring_date": hiring_date,
            "salary": salary,
            "character": character,
        }
        with driver.session() as session:
            session.write_transaction(_create_acted_in_relation, relation_data)

        flash("Actor añadido con éxito")

    return render_template("/add_actor.html", content_id=content_id)


@app.route("/add_director/<content_id>", methods=["GET", "POST"])
def add_director(content_id):
    # Get the user ID from the session
    user_id = session_flask.get("user_id")

    with driver.session() as session:
        # Query the user by ID
        user = session.read_transaction(_get_user_by_id, user_id)

    # Check if the user is logged in
    if user is None:
        return redirect(url_for("login_admin"))

    if "message" in session_flask:
        flash(session_flask["message"])
        session_flask.pop("message", None)

    if request.method == "POST":
        # Obtener los datos del formulario
        name = request.form.get("name")
        dob = datetime.strptime(request.form.get("dob"), "%Y-%m-%d").date()
        nacionality = request.form.get("nacionality")
        hiring_date = datetime.strptime(
            request.form.get("hiring_date"), "%Y-%m-%d"
        ).date()
        salary = int(request.form.get("salary"))

        id = random.randint(1, 10000000)

        # Crear la nueva película en la base de datos
        actor_data = {
            "id": id,
            "name": name,
            "nacionality": nacionality,
            "dob": dob,
        }
        with driver.session() as session:
            session.write_transaction(_add_director, actor_data)

        relation_data = {
            "content_id": content_id,
            "director_id": id,
            "hiring_date": hiring_date,
            "salary": salary,
        }
        with driver.session() as session:
            session.write_transaction(_create_directed_by_relation, relation_data)

        flash("Director añadido con éxito")

    return render_template("/add_director.html", content_id=content_id)


# Gestion de Usuarios


@app.route("/gestionar_usuarios")
def gestionar_usuarios():

    with driver.session() as session:
        # Obtener todos los usuarios de la base de datos
        users = session.read_transaction(_get_all_users)

    return render_template("/gestionar_usuarios.html", users=users)


@app.route("/add_user_admin", methods=["GET", "POST"])
def add_user_admin():
    # Get the user ID from the session
    user_id = session_flask.get("user_id")

    with driver.session() as session:
        # Query the user by ID
        user = session.read_transaction(_get_user_by_id, user_id)

    # Check if the user is logged in
    if user is None:
        return redirect(url_for("login_admin"))

    if "message" in session_flask:
        flash(session_flask["message"])
        session_flask.pop("message", None)

    if request.method == "POST":
        # Obtener los datos del formulario
        account_type = request.form.get("account_type")
        nombre_completo = request.form.get("nombre_completo")
        correo = request.form.get("correo")
        dob = datetime.strptime(request.form.get("fecha_nac"), "%Y-%m-%d").date()
        tipo_cuenta = request.form.get("tipo_cuenta")
        contrasena = request.form.get("contrasena")
        nota = request.form.get("nota")

        active = True

        if account_type == "admin":
            # Variables necesarias para una película
            id = random.randint(1, 10000000)

            # Crear la nueva película en la base de datos
            user_data = {
                "id": id,
                "name": nombre_completo,
                "email": correo,
                "dob": dob,
                "password": contrasena,
                "active": active,
            }
            with driver.session() as session:
                session.write_transaction(_add_admin, user_data)

            backlog = f"Backlog: Usuario {nombre_completo} creada por el usuario {user['u']['name']}"

            # Crear relación entre el administrador y el contenido creado
            relation_data = {
                "admin_id": user_id,
                "user_id": id,
                "fecha_de_adicion": datetime.today().date(),  # Fecha actual
                "nota": nota,  # Aquí puedes guardar una nota si es necesario
                "backlog": backlog,  # Aquí puedes guardar información sobre el backlog si es necesario
            }
            with driver.session() as session:
                session.write_transaction(_create_gestion_relation, relation_data)

            flash("Usuario creado con éxito")

        elif account_type == "customer":
            # Variables necesarias para una película
            id = random.randint(1, 10000000)

            # Crear la nueva película en la base de datos
            user_data = {
                "id": id,
                "name": nombre_completo,
                "email": correo,
                "dob": dob,
                "password": contrasena,
                "active": active,
                "account_type": account_type,
            }
            with driver.session() as session:
                session.write_transaction(_add_user, user_data)

            backlog = f"Backlog: Usuario {nombre_completo} creada por el usuario {user['u']['name']}"

            # Crear relación entre el administrador y el contenido creado
            relation_data = {
                "admin_id": user_id,
                "user_id": id,
                "fecha_de_adicion": datetime.today().date(),  # Fecha actual
                "nota": nota,  # Aquí puedes guardar una nota si es necesario
                "backlog": backlog,  # Aquí puedes guardar información sobre el backlog si es necesario
            }
            with driver.session() as session:
                session.write_transaction(_create_gestion_relation, relation_data)

            flash("Usuario creado con éxito")

    return render_template("/add_user_admin.html", user=user)


@app.route("/delete_user/<user_id>", methods=["POST"])
def delete_user(user_id):
    print(user_id)
    with driver.session() as session:
        session.write_transaction(_delete_user, user_id)
    flash("Usuario eliminado con éxito")
    return redirect(url_for("gestionar_usuarios"))


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


def get_movies(tx):
    result = tx.run("MATCH (m:Movie) RETURN m.title as title, m.image as image")
    records = [record for record in result]
    return records


def get_series(tx):
    result = tx.run("MATCH (s:Series) RETURN s.title as title, s.image as image")
    records = [record for record in result]
    # print(records)
    return records


@app.route("/movies")
def movies():
    user_id = session.get("user_id")

    with driver.session() as neo4j_session:
        movie_list = neo4j_session.read_transaction(get_movies)
        series_list = neo4j_session.read_transaction(get_series)
        watched_movies = neo4j_session.read_transaction(_get_watched_content, user_id)
        recommendations = generate_recommendations(user_id)

    return render_template(
        "home.html",
        movies=movie_list,
        series=series_list,
        watched_movies=watched_movies,
        recommendations=recommendations,
    )


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
        "CREATE (s:Content:Series {id: $id, title: $title, release_date: $release_date, genre: $genre, episode_duration: $episode_duration, total_episodes: $total_episodes, image: $image})",
        id=data.get("id"),
        title=data.get("title"),
        release_date=data.get("release_date"),
        genre=data.get("genre"),
        episode_duration=data.get("episode_duration"),
        total_episodes=data.get("total_episodes"),
        image=data.get("image"),
    )


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


def _create_acted_in_relation(tx, data):
    data["content_id"] = int(data["content_id"])  # Convert content_id to int
    data["actor_id"] = int(data["actor_id"])  # Convert content_id to int
    query = """
    MATCH (c:Content {id: $content_id})
    MATCH (a:Staff:Actor {id: $actor_id})
    CREATE (c)-[r:ACTUADO_POR {character: $character, hiring_date: $hiring_date, salary: $salary}]->(a)
    """
    tx.run(
        query,
        content_id=data.get("content_id"),
        actor_id=data.get("actor_id"),
        character=data.get("character"),
        hiring_date=data.get("hiring_date"),
        salary=data.get("salary"),
    )


def _create_directed_by_relation(tx, data):
    data["content_id"] = int(data["content_id"])  # Convert content_id to int
    data["director_id"] = int(data["director_id"])  # Convert content_id to int
    query = """
    MATCH (c:Content {id: $content_id})
    MATCH (d:Staff:Director {id: $director_id})
    CREATE (c)-[r:DIRIGIDO_POR {hiring_date: $hiring_date, salary: $salary}]->(d)
    """
    tx.run(
        query,
        content_id=data.get("content_id"),
        director_id=data.get("director_id"),
        hiring_date=data.get("hiring_date"),
        salary=data.get("salary"),
    )


@app.route("/create_content_relation", methods=["POST"])
def create_content_relation():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_create_content_relation, data)
    return jsonify({"message": "Relation created successfully"}), 201


def _create_content_relation(tx, data):
    query = """
    MATCH (a:Admin {id: $admin_id})
    MATCH (c:Content {id: $content_id})
    CREATE (a)-[r:CREATED {fecha_de_adicion: $fecha_de_adicion, nota: $nota, backlog: $backlog}]->(c)
    """
    tx.run(
        query,
        admin_id=data.get("admin_id"),
        content_id=data.get("content_id"),
        fecha_de_adicion=data.get("fecha_de_adicion"),
        nota=data.get("nota"),
        backlog=data.get("backlog"),
    )


def _create_gestion_relation(tx, data):
    data["admin_id"] = int(data["admin_id"])  # Convert content_id to int
    data["user_id"] = int(data["user_id"])  # Convert content_id to int
    print(data)
    query = """
    MATCH (a:Admin {id: $admin_id})
    MATCH (u:User {id: $user_id})
    CREATE (a)-[r:GESTIONA {fecha_de_adicion: $fecha_de_adicion, nota: $nota, backlog: $backlog}]->(u)
    """
    tx.run(
        query,
        admin_id=data.get("admin_id"),
        user_id=data.get("user_id"),
        fecha_de_adicion=data.get("fecha_de_adicion"),
        nota=data.get("nota"),
        backlog=data.get("backlog"),
    )


@app.route("/edit_content_relation", methods=["POST"])
def edit_content_relation():
    data = request.get_json()
    with driver.session() as session:
        session.write_transaction(_edit_content_relation, data)
    return jsonify({"message": "Relation created successfully"}), 201


def _edit_content_relation(tx, data):
    data["content_id"] = int(data["content_id"])  # Convert content_id to int
    query = """
    MATCH (a:Admin {id: $admin_id})
    MATCH (c:Content {id: $content_id})
    CREATE (a)-[r:EDITED {fecha_de_adicion: $fecha_de_adicion, nota: $nota, backlog: $backlog}]->(c)
    """
    tx.run(
        query,
        admin_id=data.get("admin_id"),
        content_id=data.get("content_id"),
        fecha_de_adicion=data.get("fecha_de_adicion"),
        nota=data.get("nota"),
        backlog=data.get("backlog"),
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
    content_id = int(content_id)
    result = tx.run(
        """
        MATCH (c) WHERE c.id = $content_id RETURN c
        """,
        content_id=content_id,
    )
    return result.single()


def _update_movie(tx, movie_data):
    movie_data["id"] = int(movie_data["id"])  # Convert id to int
    tx.run(
        """
        MATCH (m:Movie {id: $id})
        SET m.title = $title, m.release_date = $release_date, m.genre = $genre, m.duration = $duration, m.image = $image
        """,
        **movie_data,
    )


def _update_series(tx, series_data):
    series_data["id"] = int(series_data["id"])  # Convert id to int
    tx.run(
        """
        MATCH (s:Series {id: $id})
        SET s.title = $title, s.release_date = $release_date, s.genre = $genre, s.episode_duration = $episode_duration, s.total_episodes = $total_episodes
        """,
        **series_data,
    )


def _delete_content(tx, content_id):
    content_id = int(content_id)
    tx.run(
        """
        MATCH (c) WHERE c.id = $content_id DETACH DELETE c
        """,
        content_id=content_id,
    )


def _delete_user(tx, user_id):
    user_id = int(user_id)
    tx.run(
        """
        MATCH (u) WHERE u.id = $user_id DETACH DELETE u
        """,
        user_id=user_id,
    )


def _get_all_content(tx):
    result = tx.run("MATCH (c:Content) RETURN c")
    return [dict(record["c"]._properties) for record in result]


def _get_all_users(tx):
    result = tx.run("MATCH (u:User) RETURN u")
    return [dict(record["u"]._properties) for record in result]


def _mark_content_watched(tx, user_id, content_id):
    query = """
    MATCH (u:User {id: $user_id}), (m:Movie {id: $content_id})
    CREATE (u)-[r:WATCHED {timestamp: timestamp()}]->(m)
    """
    tx.run(query, user_id=user_id, content_id=content_id)


@app.route("/watched", methods=["POST"])
def mark_watched():
    user_id = session.get("user_id")
    content_id = request.form.get("content_id")

    print("USER ID", user_id)
    print("CONTENT ID", content_id)

    with driver.session() as neo4j_session:
        neo4j_session.write_transaction(_mark_content_watched, user_id, content_id)

    # Perform any other actions or return a different response as needed

    # For example, you can return a JSON response indicating success
    return {"message": "Content marked as watched"}


def _get_watched_content(tx, user_id):
    query = """
    MATCH (u:User {id: $user_id})-[r:WATCHED]->(m:Movie)
    RETURN m
    """
    result = tx.run(query, user_id=user_id)
    return [record["m"] for record in result]


def _get_recommendations(tx, user_id, genres):
    query = """
    MATCH (u:User {id: $user_id})
    MATCH (m2:Movie) WHERE m2.genre IN $genres AND NOT EXISTS((u)-[:WATCHED]->(m2))
    RETURN m2
    """
    result = tx.run(query, user_id=user_id, genres=genres)
    return [record["m2"] for record in result]


def generate_recommendations(user_id):
    with driver.session() as session:
        watched_content = session.read_transaction(_get_watched_content, user_id)
        genres = set(tuple(movie["genre"]) for movie in watched_content)
        recommendations = session.read_transaction(
            _get_recommendations, user_id, list(genres)
        )
    return recommendations


@app.route("/recommendations", methods=["GET"])
def get_recommendations():
    user_id = session.get("user_id")
    recommendations = generate_recommendations(user_id)
    return render_template("recommendations.html", recommendations=recommendations)


if __name__ == "__main__":
    app.run(debug=True)
