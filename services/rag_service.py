import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

KNOWLEDGE_PATH = os.path.join(
    BASE_DIR,
    "knowledge",
    "recovery_knowledge.json"
)


def load_knowledge():

    if not os.path.exists(KNOWLEDGE_PATH):
        return []

    with open(
        KNOWLEDGE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    if isinstance(data, dict):

        if "knowledge" in data:
            return data["knowledge"]

        if "documents" in data:
            return data["documents"]

        return [data]

    return data


def _document_text(document):

    if isinstance(document, str):
        return document

    return " ".join(
        str(value)
        for value in document.values()
    )


def retrieve_recovery_knowledge(
    query,
    top_k=5
):

    documents = load_knowledge()

    if not documents:
        return []

    texts = [
        _document_text(document)
        for document in documents
    ]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    matrix = vectorizer.fit_transform(
        texts
    )

    query_vector = vectorizer.transform(
        [query]
    )

    similarities = cosine_similarity(
        query_vector,
        matrix
    )[0]

    ranked_indices = similarities.argsort()[
        ::-1
    ]

    results = []

    for index in ranked_indices:

        score = float(
            similarities[index]
        )

        if score <= 0:
            continue

        document = documents[index]

        if isinstance(document, dict):

            result = dict(document)

        else:

            result = {
                "content": document
            }

        result["similarity"] = round(
            score,
            4
        )

        results.append(result)

        if len(results) >= top_k:
            break

    return results