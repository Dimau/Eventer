from AbstractTestClass import AbstractTestClass
from YandexAfishaCinemaParser import YandexAfishaCinemaParser
from Event import Event
from User import User
from Rating import Rating
from ParsingPointer import ParsingPointer


class TestYandexAfishaCinemaParser(AbstractTestClass):

    def test_parsing_page_with_one_event_in_full_mode(self, session, clear_data):
        event = self.create_event_yandexafishacinema_cinema_venom()
        parser = YandexAfishaCinemaParser(session, mode="full", page_limit=1000)
        assert parser.main(test_url="http://127.0.0.1:5000?source=yandexAfishaCinema&testcase=one_event_in_full_mode") == 2
        event_from_db = session.query(Event).first()
        self.check_equivalence_of_two_events(event, event_from_db)

    def test_parsing_four_pages_in_full_mode(self, session, clear_data):
        """
        This test case is about full mode
        The first page has only one event
        The second page has the same only one event
        The third page has two events - the same one and the new one
        The fourth page is 404
        Totally we have 2 events and 4 pages for parsing
        :param session:
        :param clear_data:
        :return:
        """
        parsing_pointer = ParsingPointer.get_parsing_pointer(source="YandexAfishaCinema", session=session)
        parsing_pointer.current_pointer = "dummy"
        session.add(parsing_pointer)
        session.commit()
        parser = YandexAfishaCinemaParser(session, mode='full', page_limit=1000)
        assert parser.main(test_url="http://127.0.0.1:5000?source=yandexAfishaCinema&testcase=four_pages_in_full_mode") == 4
        events_from_db = session.query(Event).all()
        assert len(events_from_db) == 5

    def test_parsing_page_with_bad_json_format_in_full_mode(self, session, clear_data):
        parser = YandexAfishaCinemaParser(session, mode='full', page_limit=1000)
        assert parser.main(test_url="http://127.0.0.1:5000?source=yandexAfishaCinema&testcase=page_with_bad_json_format") == 1
        events_from_db = session.query(Event).all()
        assert len(events_from_db) == 0

    def test_parsing_page_with_404_status_code(self, session, clear_data):
        parser = YandexAfishaCinemaParser(session, mode='full', page_limit=1000)
        assert parser.main(test_url="http://127.0.0.1:5000?source=yandexAfishaCinema&testcase=404") == 1
        events_from_db = session.query(Event).all()
        assert [] == events_from_db

    def test_make_url_for_second_page(self, session, clear_data):
        parser = YandexAfishaCinemaParser(session, mode='full', page_limit=1000)
        assert parser._make_url(page=2,
                                test_url=None) == "https://afisha.yandex.ru/api/events/selection/all-events-cinema?limit=20&offset=20&hasMixed=0&city=moscow"

    def test_make_url_with_test_url(self, session, clear_data):
        parser = YandexAfishaCinemaParser(session, mode='full', page_limit=1000)
        assert parser._make_url(page=1, test_url="http://127.0.0.1:5000?source=yandexAfishaCinema&testcase=404") == "http://127.0.0.1:5000?source=yandexAfishaCinema&testcase=404&page=1"
