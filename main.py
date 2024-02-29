from flask import Flask, render_template, request, redirect, jsonify
import pymongo
import turkish_rake as yucaib

app = Flask(__name__)

# MongoDB connect
client = pymongo.MongoClient()
db = client["KeywordDB"]


@app.route('/')
def home():
    return render_template("home.html")


def get_sequence(seq_name):
    sequence_document = db.counters.find_one_and_update(
        filter={"_id": seq_name},
        update={"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return sequence_document["seq"]


@app.route("/add-db", methods=["POST"])
def parse_to_db():
    try:
        corpus = request.form.get("corpus")
        keywords = yucaib.key_word_ext(corpus=corpus, keyword_count=10)

        db['Corpus'].insert_one({"corpus": corpus,
                                 "_id": get_sequence('Corpus'),
                                 'keywords': keywords})

        return redirect("/home.html" + corpus + keywords)

    except Exception as e:
        return f"An error occurred: {e}"


@app.route("/", methods=['GET'])
def keywords_paste(corpus):
    result = db.list_collections()
    return 0


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
