import sqlalchemy
from Base_class_sql_alchemy import Base
from sqlalchemy.orm import relationship
from FormattingDataRepresentation import FormattingDataRepresentation


class User(Base, FormattingDataRepresentation):
    __tablename__ = 'users'

    _id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    _telegram_id = sqlalchemy.Column(sqlalchemy.String(50))
    _name = sqlalchemy.Column(sqlalchemy.String(50))
    _last_queue_events_str = sqlalchemy.Column(sqlalchemy.String(2000))  # Here we save sorted by relevance list of events from last request in string format

    ratings = relationship("Rating", back_populates="user")

    def __init__(self, telegram_id=None, name=""):
        print("User:__init__(): enter")
        self.telegram_id = telegram_id
        self._name = name
        self.last_queue_events = []
        print("User:__init__(): telegram_id: " + self.telegram_id)

    def __repr__(self):
        return "<User _id: {}, " \
               "_telegram_id: {}, " \
               "_name: {}," \
               "_last_queue_events_str: {}>".format(self._id,
                                                    self._telegram_id,
                                                    self._name,
                                                    self._last_queue_events_str[0:20])

    @property
    def user_id(self):
        return self._id

    @property
    def telegram_id(self):
        return self._telegram_id

    @telegram_id.setter
    def telegram_id(self, value):
        self._telegram_id = str(value)

    @property
    def last_queue_events(self):
        """
        Getter for property last_queue_events
        :return:
        """
        # Empty string = empty list
        if self._last_queue_events_str == "":
            return []
        # Split string to list and conversion to integer
        # It is important to save the order of elements
        array = self._last_queue_events_str.split("|")
        for i in range(len(array)):
            print(i)
            array[i] = int(array[i])
        print("User:last_queue_events getter: value: " + str(array)[0:20])
        return array

    @last_queue_events.setter
    def last_queue_events(self, queue):
        """
        Setter for property last_queue_events (synonym for _last_queue_events_str), but for external people it works
        as a list, not a string.
        :param queue: We are waiting for a list of integers here (event id-s)
        :return:
        """
        self._last_queue_events_str = self.convert_from_iterator_to_string(queue)
        # TODO: add protection from string more than 2000 symbols
        print("User:last_queue_events setter: length value is " + str(len(self._last_queue_events_str)))
        print("User:last_queue_events setter: value: " + self._last_queue_events_str[0:20])

    def delete_previous_event_from_queue(self):
        list_of_events = self.last_queue_events
        del list_of_events[0]
        self.last_queue_events = list_of_events

    def clear_last_queue_events(self):
        self.last_queue_events = []
