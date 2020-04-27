from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

from newspaper import Article
from date_guesser import guess_date, Accuracy
from langdetect import detect, detect_langs

app = FastAPI(
	title="Article Scraper FastAPI Example Project",
	description="This is an example project using FastAPI.  This project re-implements another project built with the Flask framework.  The original Flask implementation can be found here: https://github.com/kotartemiy/extract-news-api",
	version="0.0.1"
	)

class ArticleOut(BaseModel):
	published_date: datetime = Field(None, title="The published date of the article", description="The published date of the article returned as a datetime.  The published date is a 'best guess', the accuracy and method via which the published date has been determine are also returned as part of the response.")
	published_date_method: str = Field(None, title="The method used to determine the published date", description="The method with which the published date of the article has been determined, returned as a string.  The string will be a human readable explanation of how the date was determined.")
	published_date_accuracy: str = Field(None, title="The level of accuracy for the published date", description="The level of accuracy with which the published date of the article has been determined.  The default value is None, if the date could not be determined.  If the date has been determined there are 3 levels of accuracy, partial, date, datetime.")
	source_url: str = Field(..., title="The url of the article", description="The url of the source article.  The url is set by the client when the request is made.")
	title: str = Field (None, title="The title of the article")
	title_lang: str = Field(None, title="The language used for the title of the article", description="The language used in the title of the source article.  The language is auto-detected, accuracy is not guaranteed.")
	text: str = Field(None, title="The text of the article", description="The text of the article, extracted from the article source url")
	text_lang: str = Field(None, title="The language used for the text of the article", description="The language used in the text of the source article.  The language is auto-detected, accuracy is not guaranteed.")
	authors: list = Field(None, title="The author(s) of the article", description="The author(s) of the article.")
	tags: list = Field(None, title="The tag(s) associated with the article", description="The tags(s) associated with the article.")
	meta_keywords: list = Field(None, title="The meta keywords associated with the article", description="The meta keywords associated with the article, as derived from the meta keywords tag in the head section of the article.")
	meta_description: str = Field(None, title="The meta description of the article", description="The meta desription of the article, as set in the meta_description head tag.")
	meta_lang: str = Field(None, title="The language of the article", description="The language as set in the meta_lang field present in the head tags of the article.")
	top_image: str = Field(None, title="The url for the top image from the article", description="The image in the top (mast) position from the article.  The URL of the image is returned.  The image itself is not returned.")
	meta_image: str = Field(None, title="The url for the meta image from the article", description="The image defined in the meta fields from the article.  The URL of the image is returned.  The image itself is not returned.  The meta image will be found in the og:image or og:image_url meta properties.")
	images: list = Field(None, title="The url of each image found in the article", description="A list of the images found in the article.  The image is represented by it's URL.")

	class Config:
		title = "Article"


@app.get("/v0/article", response_model=ArticleOut)
def get_article(
	url: str = Query(
		...,
		title="Article URL", 
		description="The URL of the requested article."
		)
	):

	article = Article(url)
	article.download()

	if (article.download_state == 2):
		article.parse()

		# Article
		article_response = {}
		article_response['source_url'] = article.url
		article_response['title'] = article.title
		article_response['text'] = article.text
		article_response['authors'] = list(article.authors)

		# Date Detection
		try:
			guess = guess_date(url = url, html = article.html)
			article_response['published_date'] = guess.date
			article_response['published_date_method'] = guess.method
			# Date Accuracy
			if guess.accuracy is Accuracy.PARTIAL:
				article_response['published_date_accuracy'] = 'partial'
			if guess.accuracy is Accuracy.DATE:
				article_response['published_date_accuracy'] = 'date'
			if guess.accuracy is Accuracy.DATETIME:
				article_response['published_date_accuracy'] = 'datetime'
			if guess.accuracy is Accuracy.NONE:
				article_response['published_date_accuracy'] = None
		except:
			article_response['published_date'] = article.published_date 
			article_response['published_date_method'] = None
			article_response['published_date_accuracy'] = None

		# Language Detection
		try:
			article_response['title_lang'] = detect(article.title)
		except:
			article_response['title_lang'] = None

		try:
			article_response['text_lang'] = detect(article.text)
		except:
			article_response['text_lang'] = None

		# Meta / Other
		article_response['meta_description'] = article.meta_description
		article_response['meta_lang'] = article.meta_lang
		article_response['meta_favicon'] = article.meta_favicon
		article_response['meta_keywords'] = list(article.meta_keywords)
		article_response['tags'] = list(article.tags)

		# Images
		article_response['images'] = list(article.images)
		article_response['meta_image'] = article.meta_img
		article_response['top_image'] = article.top_image


		return ArticleOut(**article_response)

	else:
		raise HTTPException(status_code=404, detail="Article was not found")