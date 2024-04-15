from flask import Flask, render_template, request, redirect, jsonify, session
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import turkish_rake as yucaib

app = Flask(__name__)
app.secret_key = 'mysecretkey'

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


@app.route("/home", methods=["POST"])
def parse_to_db():
    try:
        corpus = request.form.get("corpus")
        keywords = yucaib.key_word_ext(corpus=corpus, keyword_count=10)

        db['Corpus'].insert_one({"corpus": corpus,
                                 "_id": get_sequence('Corpus'),
                                 'keywords': keywords})

        return render_template("home.html", keywords=keywords)

    except Exception as e:
        return f"An error occurred: {e}"


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
            options = [{"text": request.form[f'option{i + 1}'], "count": 0,'survey_id': survey_id}
                       for i in range(num_options)]

            # Anket verilerini MongoDB'ye kaydet
            db["survey"].insert_one({
                "_id": survey_id ,
                "anket_basligi": anket_basligi,
                "options": options
            })

            # Başarılı bir şekilde işlendiğine dair bir yanıt gönderelim
            return jsonify({'message': 'Anket başarıyla kaydedildi!'})

        except Exception as e:
            return jsonify({'error': f'Hata oluştu: {str(e)}'})



@app.route('/cikis', methods=["GET", "POST"])
def cikis():
    session.pop('kullanici', None)
    return redirect("/", 302)




if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
