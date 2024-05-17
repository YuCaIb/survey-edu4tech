from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
import uuid


# import turkish_rake as yucaib

app = Flask(__name__)
app.secret_key = 'mysecretkey'

# MongoDB connect
client = pymongo.MongoClient()
db = client["KeywordDB"]
survey_collection = db['survey']



@app.route('/')
def home():
    surveys = list(survey_collection.find())

    return render_template("home.html", surveys=surveys)


@app.route('/survey/<survey_id>')
def survey_details(survey_id):
    # Seçilen anketi al
    survey = survey_collection.find_one({'_id': survey_id})
    comments = list(db["comments"].find({"survey_id": survey_id}))
    # Anketi html'e gönder
    return render_template('survey_detail.html', survey=survey,comments=comments)


# @app.route('/survey/<string:survey_id>')
# def survey_detail(survey_id):
#   # Get survey detail from MongoDB
#  survey_detail = db.survey.find_one({"_id": survey_id})
# return render_template('survey_detail.html', survey_detail=survey_detail)


@app.route('/update_count', methods=['POST','GET'])
def update_count():
    option_id = request.json['option_id']
    survey_id = request.json['survey_id']
    print("survey_id : ", survey_id)
    print("option_id : ", option_id)
    survey = survey_collection.find_one({'_id':survey_id})

    if survey:
        # count'u arttır
        for option in survey['options']:
            if option['id'] == option_id:
                option['count'] += 1
                break

        # Değişikliği kaydet
        survey_collection.update_one({"_id": survey_id}, {"$set": {"options": survey['options']}})
        updated_count = next(option['count'] for option in survey['options'] if option['id'] == option_id)
        return jsonify({'message': 'Count incremented successfully', 'updated_count': updated_count}), 200
    else:
        return jsonify({'error': 'Survey not found'}), 404


def get_sequence(seq_name):
    sequence_document = db.counters.find_one_and_update(
        filter={"_id": seq_name},
        update={"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return sequence_document["seq"]


# @app.route("/home", methods=["POST"])
# def parse_to_db():
#     try:
#         corpus = request.form.get("corpus")
#         keywords = yucaib.key_word_ext(corpus=corpus, keyword_count=10)
#
#         db['Corpus'].insert_one({"corpus": corpus,
#                                  "_id": get_sequence('Corpus'),
#                                  'keywords': keywords})
#
#         return render_template("home.html", keywords=keywords)
#
#     except Exception as e:
#         return f"An error occurred: {e}"


@app.route('/kayit-ol', methods=["GET", "POST"])
def uye_ol():
    if request.method == 'GET':
        return render_template("kayit-ol.html")
    else:
        # Formdan gelen verileri al
        email = request.form["email"]
        sifre = request.form["sifre"]
        adsoyad = request.form["adsoyad"]

        hashed_sifre = generate_password_hash(sifre, method='pbkdf2:sha256')

        # Verileri collection'a ekle
        db["kullanicilar"].insert_one({
            "_id": email,
            "sifre": hashed_sifre,
            "adsoyad": adsoyad
        })

        return redirect("/giris", 302)


@app.route('/giris', methods=["GET", "POST"])
def giris():
    if request.method == 'GET':
        return render_template("giris.html")
    else:
        # Formdan gelen verileri al
        email = request.form["email"]
        sifre = request.form["sifre"]

        kullanici = db["kullanicilar"].find_one({"_id": email})
        print("kullanici:", kullanici)

        if kullanici and check_password_hash(kullanici["sifre"], sifre):
            session['kullanici'] = kullanici
            return redirect("/", 302)
        else:
            return "Kullanıcı bulunamadı ya da şifre geçersiz"


@app.route('/add-comment/<survey_id>', methods=['POST'])
def add_comment(survey_id):
    try:
        author = request.form['author']
        email = request.form['email']
        content = request.form['content']

        comment = {
            "survey_id": survey_id,
            "author": author,
            "email": email,
            "content": content
        }

        db["comments"].insert_one(comment)

        return redirect(url_for('survey_details', survey_id=survey_id))
    except Exception as e:
        return jsonify({'error': f'Hata oluştu: {str(e)}'})


@app.route('/create-survey', methods=['GET', 'POST'])
def survey():
    if request.method == 'GET':
        return render_template('create-survey.html')
    elif request.method == 'POST':
        try:
            # Form verilerini al
            name = request.form['name']
            email = request.form['email']
            anket_basligi = request.form['anket-basligi']

            # Oylama maddelerini al
            num_options = int(request.form['numOptions'])
            survey_id = uuid.uuid1().hex
            options = [
                {"text": request.form[f'option{i + 1}'], "count": 0, 'survey_id': survey_id, 'id': uuid.uuid1().hex}
                for i in range(num_options)]

            # Anket verilerini MongoDB'ye kaydet
            db["survey"].insert_one({
                "yazar_adi": name,
                "e-mail": email,
                "_id": survey_id,
                "anket_basligi": anket_basligi,
                "options": options,
            })

            # Başarılı bir şekilde işlendiğine dair bir yanıt gönderelim
            return redirect(url_for('survey_details', survey_id=survey_id))

        except Exception as e:
            return jsonify({'error': f'Hata oluştu: {str(e)}'})


@app.route('/cikis', methods=["GET", "POST"])
def cikis():
    session.pop('kullanici', None)
    return redirect("/", 302)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
