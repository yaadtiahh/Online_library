import requests
import os
import argparse
import time
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlparse


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def download_txt(response, filename, result_folder="Result", folder='books/'):
    Path(result_folder).mkdir(parents=True, exist_ok=True)

    filename = sanitize_filename(filename)
    dest_folder = f"{result_folder}/{folder}"
    Path(dest_folder).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(dest_folder, filename)
    with open(filepath, 'wb') as file:
        file.write(response.content)


def download_image(url, result_folder="Result", folder='images/'):
    Path(result_folder).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()

    url = urlparse(url)
    fname = url.path.split("/")[-1]
    dest_folder = f"{result_folder}/{folder}"
    Path(dest_folder).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(dest_folder, fname)

    with open(filepath, 'wb') as file:
        file.write(response.content)


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.select_one('h1')
    title_tag = title_tag.text.split('::')
    name = title_tag[0].strip()
    author = title_tag[1].strip()

    comment_block = soup.select(".texts")
    comments = [comment.select_one(".black").text for comment in comment_block]

    genre_block = soup.select(".d_book")
    genres = genre_block[1].select('a')
    books_genres = [genre.text for genre in genres]

    book_url = soup.select_one(".bookimage img")['src']

    book_parameters = {
        "name": name,
        "author": author,
        "comments": comments,
        "genres": books_genres,
        "book_url": book_url,
    }
    return book_parameters


def main():
    parser = argparse.ArgumentParser(
        description='Данная программа берет книги сайта tululu.org и скачивает их(текст и картинки книг)'
    )
    parser.add_argument('--start_page', help="Начальное id", type=int, default=1)
    parser.add_argument('--end_page', help="Конечное id", type=int, default=11)

    args = parser.parse_args()

    for book_number in range(args.start_page, args.end_page):
        payload = {
            "id": book_number
        }
        url = "https://tululu.org/txt.php"

        try:
            response = requests.get(url, params=payload)
            response.raise_for_status()
            check_for_redirect(response)

            book_url = f'https://tululu.org/b{book_number}/'
            page_response = requests.get(url)
            page_response.raise_for_status()
            check_for_redirect(page_response)

            book_parameters = parse_book_page(page_response)
            print(book_parameters['book_url'])
            filename = f'{book_number}. {book_parameters["name"]}.txt'
            download_txt(response, filename)

            photo_url = urljoin(book_url, book_parameters["book_url"])
            download_image(photo_url)

        except requests.exceptions.HTTPError:
            print("Такой страницы не сущетсвует!")
        except requests.exceptions.ConnectionError:
            print('Соединение разорвано!')
            time.sleep(10)


if __name__ == '__main__':
    main()
