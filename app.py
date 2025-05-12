import pickle
import streamlit as st
import requests
import gdown
import os
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from functools import lru_cache

# Configure retries for transient errors
session = requests.Session()
retries = Retry(
    total=3,  # Maximum number of retries
    backoff_factor=1,  # Delay between retries (1s, 2s, 4s, etc.)
    status_forcelist=[500, 502, 503, 504]  # Retry on these status codes
)
session.mount('https://', HTTPAdapter(max_retries=retries))



@lru_cache(maxsize=512)
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8"
        response = session.get(url, timeout=5)  # Use session with retries
        response.raise_for_status()  # Raise HTTPError for bad status codes

        data = response.json()
        poster_path = data.get("poster_path")

        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
        else:
            # Poster not found in API response
            return "https://via.placeholder.com/500x750?text=Poster+Not+Found"

    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching poster for ID {movie_id}: {str(e)}")
        return "https://via.placeholder.com/500x750?text=Error+Loading+Poster"
    except KeyError:
        return "https://via.placeholder.com/500x750?text=Invalid+API+Response"


def recommend(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
    except IndexError:
        st.error("Movie not found in database!")
        return [], []

    distances = sorted(enumerate(similarity[index]), key=lambda x: x[1], reverse=True)

    recommended_movies = []
    recommended_posters = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].id
        poster_url = fetch_poster(movie_id)
        recommended_posters.append(poster_url)
        recommended_movies.append(movies.iloc[i[0]].title)

    return recommended_movies, recommended_posters



# Google Drive file ID (from the shareable link)
file_id = "similarity.pkl"
url = f"https://drive.google.com/file/d/12AAt0lBVkSM9kVIW2a-pp6wg4BZsYh17/view?usp=sharing/uc?id={file_id}"
# Local path to save the file
output_path = "similarity.pkl"

# Download the file if it doesn't exist
if not os.path.exists(output_path):
    gdown.download(url, output_path, quiet=False)

# Load the file
with open(output_path, "rb") as f:
    similarity = pickle.load(f)

st.header('Movie Recommender System')
movies = pd.read_csv('movies.csv')
# similarity = pickle.load(open('similarity.pkl', 'rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox("Type or select a movie from the dropdown", movie_list)

if st.button('Show Recommendation'):
    names, posters = recommend(selected_movie)
    cols = st.columns(5)
    for col, name, poster in zip(cols, names, posters):
        with col:
            st.text(name)
            st.image(poster)