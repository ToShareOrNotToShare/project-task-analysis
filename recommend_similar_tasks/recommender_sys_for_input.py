import pandas as pd
import numpy as np
import re
import time
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

def cleaner(text):
    
    """ lowercase and tokenize text, keep only alphabetical chars 

    Args: 
        text            (string):      text to clean
    Returns:
        text            (string):      cleaned text

    """
    
    
    text = str(text).lower()
    # adding numbers to regex, possibly information like "BKR01" as location is helpful
    text = re.sub('[^A-Za-z0-9]', ' ', text)
    text = word_tokenize(text)
    text = [token for token in text if token not in stopwords.words('english')]
    
    
    return " ".join(text)


def dataframe_column_to_cosine_sim(df, column):

    """Prints customized welcome string based on time

    Args: 
        df              (obj):      DataFrame
        column          (string):   Name of the column

    Returns:
        corpus          (list):     list of documents as strings
        tf_idf_matrix   (obj):      scipy sparse tf-idf matrix
        cosine_sim      (array):    cosine similarity matrix

    """
    start = time.time()
    
    # convert dataframe strings into list of strings
    corpus = df[column].tolist()
    
    # use english stop words
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    
    # generate tf-idf vectors for corpus
    tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)
    
    # compute similarity matrix with pairwise scores, faster version
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    end = time.time()

    # get total time formatted as float
    print(f'Time taken for cosine calculations is {(end-start):.4f} seconds')
    
    
    return corpus, tfidf_matrix, cosine_sim


def get_recommendations(title, cosine_sim, df, column, top_n):

    """Create item recommendations based on cosine similarity

    Args: 
        title           (string):   Item name
        cosine_sim      (array):    cosine similarity matrix
        df              (obj):      DataFrame
        column          (string):   Column name
        top_n           (int):      amount of similar observations, 1 < top_n < 20

    Returns:
        df              (obj):      DataFrame with top n recommendations

    """
    # check input value for top_n to be smaller than 20
    try:
        assert top_n < 20
        assert top_n > 1
    except:
        raise ValueError('Wrong value for top_n. Enter a valid value.')

    # adjust index for searching
    df.reset_index(inplace=True, drop=True)

    # generate mapping between titles and index
    indices = pd.Series(df.index, index=df[column])

    # get index of item that matches title
    idx = indices[title]

    # sort the items based on the similarity scores
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # get the scores for n most similar items
    sim_scores = sim_scores[1:top_n+1]

    # get the item indices
    item_indices = [i[0] for i in sim_scores]

    # return the top n most similar items
    return df[['ID',column,'Deadline']].iloc[item_indices]

def initialize_frame_for_recommender(df, title, column, top_n, new_string = False):

    """Prepare a dataframe and return recommendations

    Args: 
        df              (obj):      DataFrame with tasks
        title           (string):   Item name
        column          (string):   Column name
        top_n           (int):      Amount of similar observations
        new_string      (bool):     If new title is being added to the dataframe

    Returns:
        df              (obj):      DataFrame with top n recommendations

    """
    cleaned_title = ''

    if new_string:

        cleaned_title = cleaner(title)

        # case the entered input does not yield enough words
        if len(cleaned_title.split()) < 2:
            raise IOError(f'You have entered a too short amount of data. Please use different and more words than {title}.')

        # create new row based on the entered string
        new_row = pd.DataFrame([[999,title,'0','You want to?',]], columns=df.columns.tolist(), index=[0])

        # add that row to df
        df = df.append(new_row, ignore_index = True)

    df['cleaned_column'] = df[column].apply(lambda x: cleaner((str(x))))

    #### corner case, what if entered text is exactly something that was already in the dataframe?
    if cleaned_title and cleaned_title in df['cleaned_column'].tolist()[:-1]:
        raise ValueError(f'Inserted same task as existing one. Please change input. \n Inserted {title}')

    # prepare text 
    corpus, tfidf_matrix, cosine_sim = dataframe_column_to_cosine_sim(df, 'cleaned_column')

    return get_recommendations(title, cosine_sim, df, column, top_n)
