from neo4j import GraphDatabase

neo4j_uri = "neo4j+s://2144e45a.databases.neo4j.io"
neo4j_user = "neo4j"
neo4j_password = "0VbP5DwbQ2y7YcwKoGKB3vX06a8VnZiwNZp62KXyj_0"

# Initialize the connection to Neo4j
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))


def load_csv_file(tx, file_url):
    query = f"""
    LOAD CSV WITH HEADERS FROM 'https://drive.google.com/file/d/1VLd26YLaA3-VwR6ErNnmjmV2HuDYXC4r/view?usp=sharing' AS row
    MERGE (n:Movie {id: toInteger(row.id), title: row.title, release_date: row.release_date, genre: row.genre, duration: toInteger(row.duration), image: row.image})
    RETURN n
    """
    tx.run(query)


def import_movies_csv():
    with driver.session() as session:
        session.write_transaction(
            load_csv_file,
            "https://drive.google.com/file/d/1VLd26YLaA3-VwR6ErNnmjmV2HuDYXC4r/view?usp=sharing",
        )


if __name__ == "__main__":
    import_movies_csv()
