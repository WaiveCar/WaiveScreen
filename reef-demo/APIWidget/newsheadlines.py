from cached_request import request

url = 'https://newsapi.org/v2/top-headlines'
API_KEY = 'e80379b7b0854500a9b9dadb139ce9a5'


def get_news_stories(num=5):
    """
    Gets a maximum of <num> news stories.

    Args:
        num: max number of news stories to return, default=5
    Returns:
        0 on unsuccessful request
        list of articles in the form of dictionaries with the following keys:
            source_name - news source name (ex: USA Today)
            title - article headline
            image_url - link to the headline photo
            description - brief description of the news story
            date - date of article publication
    """
    params = {'country': 'us', 'apiKey': API_KEY}
    response = request('GET', url=url, params=params)
    res = None
    if not isinstance(response, dict):
        if response.status_code != 200:
            return 0
        res = response.json()
    else: res = response

    articles = []
    for i in range(0, min(num, len(res['articles']))):
        article = {
            'source_name': res['articles'][i]['source']['name'],
            'title': res['articles'][i]['title'],
            'image_url': res['articles'][i]['urlToImage'],
            'description': res['articles'][i]['description'],
            'date': res['articles'][i]['publishedAt']
        }
        articles.append(article)
    return articles
