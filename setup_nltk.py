import nltk
import os

def setup_nltk():
    # Define the path where NLTK data should be downloaded
    nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")
    if not os.path.exists(nltk_data_path):
        os.makedirs(nltk_data_path)
    
    # Download NLTK data
    nltk.download('punkt', download_dir=nltk_data_path)
    nltk.download('stopwords', download_dir=nltk_data_path)

if __name__ == "__main__":
    setup_nltk()
