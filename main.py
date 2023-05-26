from flask import Flask, render_template
from neo4j import GraphDatabase

app = Flask(__name__)

aura_url = "bolt://neo4j_uri"
user = "neo4j_user"
password = "neo4j_password"

# Cambia esto por tu propia clave secreta
app.config['SECRET_KEY'] = 'tu_clave_secreta'
driver = GraphDatabase.driver(aura_url, auth=(user, password))


@app.route('/')
def login_register():
    return render_template('/login.html')


if __name__ == '__main__':
    app.run(debug=True)
