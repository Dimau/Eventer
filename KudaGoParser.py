# -*- coding: utf-8 -*-

import requests
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from Event import Event

engine = sqlalchemy.create_engine("mysql://eventer:88nJnmd446HbngYh-DDvb@localhost/eventer?charset=utf8", echo=False)
Session = sessionmaker(bind=engine)
session = Session()


class KudaGoParser:

    def main(self):
        """
        Метод скачивает списки событий (перебирает параметр page), и записывает новые данные в БД,
        пока не будет достигнут id последнего ранее успешно обработанного объявления
        :return:
        """
        last_handled_id_from_base = self.get_last_handled_id()

        page_number = 1
        old_event_in_collection = False
        while True:
            url = self.make_url(page=page_number)
            url_content = self.get_url_content(url)
            events_collection_source = self.list_parser(url_content)

            # Перебираем события из списка и формируем нормализованные словари под каждое отдельное событие
            events_collection_final = []
            for item in events_collection_source:
                if item['id'] <= int(last_handled_id_from_base):
                    old_event_in_collection = True
                    continue
                event = self.item_parser(item)
                events_collection_final.append(event)

            # Новый набор событий с сайта записываем в базу
            self.write_events_to_db(events_collection_final)

            # Список событий отсортирован по убыванию id, если в новой выборке есть хотя бы 1 событие,
            # которое уже есть в базе, то дальше перебирать страницы нет смысла
            if old_event_in_collection or page_number == 4:
                break

            page_number = page_number + 1

    @staticmethod
    def list_parser(url_content):
        """
        Метод возвращает коллекцию из событий с данной страницы
        :return: 
        """
        url_content_json = url_content.json()
        return url_content_json['results']

    @staticmethod
    def item_parser(item):
        """
        Достает поля, нужные для сохранения события в БД
        :param item:
        :return:
        """
        event = {}
        event['id_kudago'] = item['id']
        event['title'] = item['title']
        event['description'] = item['description']
        event['url'] = 'https://kudago.com/' + item['location']['slug'] + '/event/' + item['slug']
        event['categories_kudago'] = item['categories'][0]
        event['tags_kudago'] = item['tags']
        return event

    @staticmethod
    def get_last_handled_id():
        """
        Возвращает самый большой id_kudago из базы (последнее сохраненное в БД мероприятие с этого сайта)
        :return:
        """
        try:
            last_handled_id_tuple = session.query(Event.id_kudago).order_by(Event.id_kudago)[-1]
        except IndexError:
            last_handled_id_tuple = (0,)
        return last_handled_id_tuple[0]

    @staticmethod
    def get_url_content(url):
        """
        Возвращает объект ответа с полным html текстом страницы (или JSON словарем) по переданному url
        :param url:
        :return:
        """
        req = requests.get(url)
        return req

    @staticmethod
    def make_url(page):
        """
        Собирает урл для получения страницы со списком мероприятий
        :return:
        """
        url_template = 'https://kudago.com/public-api/v1.4/events/?' \
            'lang=%(lang)s&' \
            'page_size=%(page_size)s&' \
            'order_by=%(order_by)s&' \
            'text_format=%(text_format)s&' \
            'location=%(location)s&' \
            'is_free=%(is_free)s&' \
            'fields=%(fields)s&' \
            'page=%(page)s'

        url = url_template % {
            'lang': 'ru',
            'page_size': '10',
            'order_by': "-id",
            'text_format': 'html',
            'location': 'msk',
            'is_free': '0',
            'fields': 'id,dates,title,short_title,slug,place,description,body_text,location,categories, \
            tagline,age_restriction,price,is_free,images,favorites_count,comments_count,site_url,tags,participants',
            'page': page
        }
        return url

    @staticmethod
    def write_events_to_db(events_collection_normalized):
        for item in events_collection_normalized:
            event = Event(item)
            session.add(event)
        session.commit()


if __name__ == '__main__':

    parser = KudaGoParser()
    parser.main()
