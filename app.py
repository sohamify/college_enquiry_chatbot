from flask import Flask, request, jsonify
import random
import json
import pickle
import numpy as np
from tensorflow.keras.models import load_model
from gensim.models import Word2Vec
import spacy
from flask_cors import CORS

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Load trained chatbot model
model = load_model("chatbot_model.h5")

# Load Word2Vec model
w2v_model = Word2Vec.load("word2vec.model")

# Load intents
with open("intents.json", "r", encoding="utf-8") as file:
    intents = json.load(file)

# Load words and classes
words = pickle.load(open("words.pkl", "rb"))
classes = pickle.load(open("classes.pkl", "rb"))

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Function to convert sentence to Word2Vec vector
def sentence_to_vector(sentence, model):
    doc = nlp(sentence.lower())
    vectors = [model.wv[token.lemma_] for token in doc if token.lemma_ in model.wv]
    
    if vectors:
        return np.mean(vectors, axis=0)  # Average word vectors
    else:
        return np.zeros(model.vector_size)  # Return zero vector if no words found

# Function to predict intent
def predict_intent(sentence):
    vector = sentence_to_vector(sentence, w2v_model).reshape(1, -1)
    predictions = model.predict(vector)[0]
    
    ERROR_THRESHOLD = 0.25
    results = [[i, p] for i, p in enumerate(predictions) if p > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)

    return [{"intent": classes[r[0]], "probability": str(r[1])} for r in results]

# Function to generate chatbot response
def chatbot_response(sentence):
    intents_list = predict_intent(sentence)
    if intents_list:
        tag = intents_list[0]["intent"]
        for intent in intents["intents"]:
            if intent["tag"] == tag:
                return random.choice(intent["responses"])
    return "I'm not sure how to answer that."

# Define API route
@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    
    response = chatbot_response(user_message)
    return jsonify({"response": response})

# Run Flask server
if __name__ == "__main__":
    app.run(debug=True)
