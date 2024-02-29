from rake_nltk import Rake


turkish_set = set(line.strip() for line in open('turkce-stop-words.txt', encoding="utf8"))
r = Rake(stopwords=turkish_set, language='turkish')


def key_word_ext(corpus: str, keyword_count: int):
    """
    ------
    Params
    corpus: string
            sentence you want to extract keyword in it, only works with Turkish
    keyword_count: int
                   Keyword count you want to extract.
    ----
    :return keyword_list
    """
    r.extract_keywords_from_text(corpus)
    keyword_list = []
    ranked_list = r.get_ranked_phrases_with_scores()
    for keyword in ranked_list:
        keyword_updated = keyword[1].split()
        keyword_updated_string = " ".join(keyword_updated[:2])
        keyword_list.append(keyword_updated_string)
        if len(keyword_list) > keyword_count:
            break

    return keyword_list

