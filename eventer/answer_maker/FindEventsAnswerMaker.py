from answer_maker.AbstractAnswerMaker import AbstractAnswerMaker
from Event import Event
from Rating import Rating
from Sorter import Sorter
import datetime
import logging


class FindEventsAnswerMaker(AbstractAnswerMaker):

    def __repr__(self):
        return "<FindEventsAnswerMaker intent: {}, result_of_classification: {}>".format(self.intent, str(self.result_of_classification))

    def get_answer(self):

        # Intent will be useful for view functions
        answer = {"intent": self.intent}

        # Prepare all necessary data
        target_categories = self._get_categories_for_type_of_action()
        logging.info("Target categories: %s", target_categories)
        start_timestamp, finish_timestamp = self._get_required_time_period()
        logging.info("Required time period: %s - %s or %s - %s", start_timestamp, finish_timestamp,
                     datetime.datetime.fromtimestamp(start_timestamp),
                     datetime.datetime.fromtimestamp(finish_timestamp))
        free_of_charge = True if self.result_of_classification['free_or_not'] == "free" else False
        logging.info("Free_of_charge: %s", free_of_charge)
        with_who = self.result_of_classification['with_who']
        logging.info("With_who: %s", with_who)

        # Extracting sorted relevant events
        relevant_events = self._get_sorted_events_for_conditions(start_timestamp, finish_timestamp,
                                                                 target_categories, free_of_charge, with_who)
        logging.info('Size of sorted list of relevant events: %s', len(relevant_events))
        if not relevant_events:
            answer["text"] = "Я не нашел новых событий под эти условия, давайте поищем что-нибудь еще?"
            answer["status"] = "none_event"
            self.user.clear_last_queue_events()
            return answer
        answer.update(self.make_one_event_data_card(relevant_events[0]))

        # We have to save the sorted list of relevant events for the user
        self.user.last_queue_events = self._get_id_for_events_in_iterator(relevant_events)
        self.session.add(self.user)
        self.session.commit()
        return answer

    def _get_categories_for_type_of_action(self):
        """
        Список возможных типов действий, которые мы можем распознать во фразе пользователя задается в dialogflow
        Этот список может отличаться от набора тегов, присваиваемых событиям в базе данных, так как
        под одно понятие пользователя могут подходить несколько тегов в базе данных, например:
        night = night и party, comedy-club = comedy-club и stand-up и так далее.
        При этом во фразе пользователя по 1 слове мы можем выделить только какую-то одну категорию,
        отсюда и отношение: один во фразе пользовател ко многим в базе данных.
        :param type_of_action:
        :return:
        """

        type_of_action = self.result_of_classification['type-of-action']

        if type_of_action == "":
            return set()

        type_of_action_dictionary = {
            "concert": ["concert"],
            "theater": ["theater"],
            "education": ["education"],
            "party": ["party"],
            "sport": ["sport"],
            "exhibition": ["exhibition", "permanent-exhibitions"],
            "tour": ["tour"],
            "festival": ["festival"],
            "cinema": ["cinema"],
            "fashion": ["fashion"],
            "show": ["show"],
            "social-activity": ["social-activity"],
            "games": ["games"],
            "night": ["night"],
            "meeting": ["meeting"],
            "speed-dating": ["speed-dating"],
            "flashmob": ["flashmob"],
            "masquerade": ["masquerade", "festival"],
            "romance": ["romance"],
            "dance-trainings": ["dance-trainings"],
            "evening": ["evening"],
            "discount": ["discount"],
            "stock": ["stock"],
            "sale": ["sale"],
            "shopping": ["shopping"],
            "quest": ["quest"],
            "yoga": ["yoga"],
            "presentation": ["presentation"],
            "magic": ["magic"],
            "kvn": ["kvn"],
            "comedy-club": ["comedy-club"],
            "stand-up": ["stand-up"],
            "kids": ["kids"],
            "circus": ["circus"],
            "open": ["open"],
            "other": ["other"],
            "photo": ["photo"],
            "global": ["global"],
            "business-events": ["business-events"]
        }
        return set(type_of_action_dictionary.get(type_of_action, []))

    def _get_required_time_period(self):
        # Manage with dates
        if self.result_of_classification['date_period']:
            dates = self.result_of_classification['date_period'].split("/")
            start_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d")  # '2018-07-28/2018-07-29'
            finish_date = datetime.datetime.strptime(dates[1], "%Y-%m-%d")  # '2018-07-28/2018-07-29'
        elif self.result_of_classification['date']:
            start_date = datetime.datetime.strptime(self.result_of_classification['date'], "%Y-%m-%d")  # '2018-07-28'
            finish_date = start_date
        elif self.result_of_classification['time_period']:
            start_date = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)  # begin of current date
            finish_date = start_date
        else:
            start_date = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)  # begin of current date
            finish_date = start_date + datetime.timedelta(weeks=4)

        # Manage with time
        if self.result_of_classification['date_period']:
            start_timestamp = start_date.timestamp()
            finish_timestamp = (finish_date + datetime.timedelta(hours=23, minutes=59)).timestamp()
        elif self.result_of_classification['time_period']:
            times = self.result_of_classification['time_period'].split("/")  # '16:00:00/23:59:00'
            start_times = times[0].split(":")  # '16:00:00'
            finish_times = times[1].split(":")  # '23:59:00'
            start_time_delta = datetime.timedelta(hours=int(start_times[0]), minutes=int(start_times[1]), seconds=int(start_times[2]))
            finish_time_delta = datetime.timedelta(hours=int(finish_times[0]), minutes=int(finish_times[1]), seconds=int(finish_times[2]))
            start_timestamp = (start_date + start_time_delta).timestamp()
            finish_timestamp = (finish_date + finish_time_delta).timestamp()
        else:
            start_timestamp = start_date.timestamp()
            finish_timestamp = (finish_date + datetime.timedelta(hours=23, minutes=59)).timestamp()

        # Correction for current time
        start_timestamp, finish_timestamp = self._time_correction_for_current_time(start_timestamp=start_timestamp,
                                                                                   finish_timestamp=finish_timestamp)

        # Correction for local time
        start_timestamp, finish_timestamp = self._time_correction_for_local_time(start_timestamp=start_timestamp,
                                                                                 finish_timestamp=finish_timestamp)
        return int(start_timestamp), int(finish_timestamp)

    @staticmethod
    def _time_correction_for_current_time(start_timestamp=0.0, finish_timestamp=0.0):
        """
        Start time has to be more than current server time.
        If finish time least than current time, than we will take next 24 hours.
        :param start_timestamp:
        :param finish_timestamp:
        :return:
        """
        # TODO: refactoring 3 - will have be in config file
        if start_timestamp < (datetime.datetime.now() + datetime.timedelta(
                hours=3)).timestamp():  # server time is least for 3 hours than real moscow time
            start_timestamp = (datetime.datetime.now() + datetime.timedelta(hours=3)).timestamp()
        if finish_timestamp < (datetime.datetime.now() + datetime.timedelta(hours=3)).timestamp():
            finish_timestamp = (datetime.datetime.now() + datetime.timedelta(hours=23, minutes=59)).timestamp()
        return start_timestamp, finish_timestamp

    @staticmethod
    def _time_correction_for_local_time(start_timestamp=0.0, finish_timestamp=0.0):
        """
        User tell us time as his local time, but events id database are saved with UTC timestamp
        this method convert required user local time to UTC time for work with database
        :param start_timestamp:
        :param finish_timestamp:
        :return:
        """
        return start_timestamp - 3600 * 3, finish_timestamp - 3600 * 3  # only for Moscow timezone

    def _get_events_for_conditions(self, start_timestamp, finish_timestamp, categories, free_of_charge):
        """
        Return set of events that is fitting for user request by category, date and other conditions (NOT SORTED BY RELEVANCE)!!!
        :param start_timestamp:
        :param finish_timestamp:
        :param categories:
        :param free_of_charge: bool (True - only free of charge events, False - all events)
        :return: list of Events
        """
        relevant_events = set()
        if len(categories) != 0:  # if user writes something about categories
            for category in categories:
                relevant_events.update(self.session.query(Event).filter(
                    Event._categories.like("%" + category + "%"),
                    Event._start_time >= start_timestamp,
                    Event._start_time <= finish_timestamp
                ).all())
        else:  # if user doesn't write something about categories
            relevant_events.update(self.session.query(Event).filter(
                Event._start_time >= start_timestamp,
                Event._start_time <= finish_timestamp
            ).all())
        logging.info("Size of set of relevant events: %s", len(relevant_events))
        if free_of_charge:
            relevant_events = self._remove_chargeable_events(relevant_events)
        relevant_events = self._replace_duplicates_for_main_event(relevant_events)
        relevant_events = self._remove_evaluated_events(relevant_events)
        return list(relevant_events)

    def _remove_chargeable_events(self, relevant_events):
        result_set_of_events = set()
        removed_events = []
        for event in relevant_events:
            if event.price_min == 0 and event.price_max == 0:
                result_set_of_events.add(event)
            else:
                removed_events.append(event.event_id)
        logging.info('Removed chargeable events: %s', removed_events)
        return result_set_of_events

    def _remove_evaluated_events(self, relevant_events):
        ids_evaluated_events = set()
        for event_id, in self.session.query(Rating._event_id).filter(Rating._user_id == self.user.user_id):
            ids_evaluated_events.add(event_id)
        result_set_of_events = set()
        removed_events = []
        for event in relevant_events:
            if event.event_id in ids_evaluated_events:
                removed_events.append(event.event_id)
                continue
            result_set_of_events.add(event)
        logging.info('Removed events (amount = %s): %s', len(removed_events), removed_events)
        return result_set_of_events

    def _replace_duplicates_for_main_event(self, relevant_events):
        """
        Take set of events, removes from it all duplicates and replaces them by latest main event in every series
        :param relevant_events:
        :return:
        """
        result_set_of_events = set()
        duplicate_events = []
        id_main_events = set()  # for optimization amount of requests to database
        for event in relevant_events:
            if not event.duplicate_id:
                result_set_of_events.add(event)
                continue
            duplicate_events.append(event.event_id)
            if event.duplicate_id in id_main_events:
                continue
            main_event = self.session.query(Event).filter(Event._id == event.duplicate_id).first()
            id_main_events.add(main_event.event_id)
            result_set_of_events.add(main_event)
        logging.info('Replaced duplicate events (amount of duplicates = %s, amount of remaining events = %s): %s',
                     len(duplicate_events), len(result_set_of_events), duplicate_events)
        return result_set_of_events

    def _get_sorted_events_for_conditions(self, start_timestamp, finish_timestamp, categories, free_of_charge, with_who):
        """
        Return sorted list of relevant events that is fitting for user request
        MAXIMUM 100 events per time
        :param start_timestamp:
        :param finish_timestamp:
        :param categories:
        :return: sorted list of Events
        """
        relevant_events = self._get_events_for_conditions(start_timestamp, finish_timestamp, categories, free_of_charge)
        sorter = Sorter(self.session, self.user, relevant_events, categories, free_of_charge, with_who)
        sorted_events = sorter.get_sorted_events()
        return sorted_events[0:100]  # we will return for one time only 100 most relevant events

    @staticmethod
    def _get_id_for_events_in_iterator(iterator):
        list_of_id = []
        for item in iterator:
            list_of_id.append(item.event_id)
        return list_of_id
