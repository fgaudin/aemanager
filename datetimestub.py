import datetime as datetime_orig

class DatetimeStub(object):
    """
    A datetimestub object to replace methods and classes from
    the datetime module.

    Usage:
        import sys
        sys.modules['datetime'] = DatetimeStub()
    """
    class datetime(datetime_orig.datetime):
        mock_year = 2010
        mock_month = 10
        mock_day = 25

        @classmethod
        def now(cls):
            """
            Override the datetime.now() method to return a
            datetime one year in the future
            """
            result = datetime_orig.datetime.now()
            return result.replace(year=cls.mock_year, month=cls.mock_month, day=cls.mock_day)

    class date(datetime_orig.date):
        mock_year = 2010
        mock_month = 10
        mock_day = 25

        @classmethod
        def today(cls):
            """
            Override the date.today() method to return a
            date one year in the future
            """
            result = datetime_orig.date.today()
            return result.replace(year=cls.mock_year, month=cls.mock_month, day=cls.mock_day)


    def __getattr__(self, attr):
        """
        Get the default implementation for the classes and methods
        from datetime that are not replaced
        """
        return getattr(datetime_orig, attr)

