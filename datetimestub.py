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

        @classmethod
        def now(cls):
            """
            Override the datetime.now() method to return a
            datetime one year in the future
            """
            result = datetime_orig.datetime.now()
            return result.replace(year=2010, month=10, day=25)

    class date(datetime_orig.date):
        @classmethod
        def today(cls):
            """
            Override the date.today() method to return a
            date one year in the future
            """
            result = datetime_orig.date.today()
            return result.replace(year=2010, month=10, day=25)


    def __getattr__(self, attr):
        """
        Get the default implementation for the classes and methods
        from datetime that are not replaced
        """
        return getattr(datetime_orig, attr)

