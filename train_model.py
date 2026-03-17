Python 3.10.8 (tags/v3.10.8:aaaf517, Oct 11 2022, 16:50:30) [MSC v.1933 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
>>> import pandas as pd
... import pickle
... from sklearn.model_selection import train_test_split
... from sklearn.feature_extraction.text import TfidfVectorizer
... from sklearn.linear_model import LogisticRegression
... from sklearn.pipeline import Pipeline
... 
... # 1. Load Dataset (Download from Kaggle link first)
... df = pd.read_csv('IMDB Dataset.csv') # Ensure file is in the same folder
... 
... # 2. Preprocessing
... df['sentiment'] = df['sentiment'].map({'positive': 1, 'negative': 0})
... 
... # 3. Create a Pipeline (Vectorization + Model)
... model_pipeline = Pipeline([
...     ('tfidf', TfidfVectorizer(stop_words='english', max_features=5000)),
...     ('clf', LogisticRegression())
... ])
... 
... # 4. Train Model
... X_train, X_test, y_train, y_test = train_test_split(df['review'], df['sentiment'], test_size=0.2)
... model_pipeline.fit(X_train, y_train)
... 
... # 5. Save the model for the website
... with open('movie_model.pkl', 'wb') as f:
...     pickle.dump(model_pipeline, f)
... 
