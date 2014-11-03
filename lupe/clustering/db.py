import os

DATABASE_SETTINGS = {
    'driver': 'psycopg2', # sqlite3 or psycopg2

    # For sqlite, name of DB file.
    # For postgres, name of database.
    'database': 'lupe.db', # postgres
    'username': 'lupe', # postgres only
    'password': 'lupe', # postgres only
    'host': None, # postgres only, if the DB is on a different machine
    'port': 5432, # postgres only, this is the default value.
}

DB_DRIVER = __import__(DATABASE_SETTINGS['driver'], globals(), locals(), [], -1)

class Database(object):

    def __init__(self):
        self.connection = None
        if not self.is_sqlite() and not self.is_postgres():
            raise ValueError("Unsupported Database Driver: "
                             + DATABASE_SETTINGS['driver'])

    @property
    def settings(self):
        return DATABASE_SETTINGS

    @property
    def wildcard(self):
        '''engine-specific character sequence to indicate query parameters
           in SQL statments.'''

        if self.is_sqlite():
            return '?'
        elif self.is_postgres():
            return '%s'

    @property
    def exception_error_class(self):
        return DB_DRIVER.Error

    def escape_symbol(self, symbol):
        if symbol.literal:
            return self.wildcard

        if self.is_sqlite():
            return symbol.value
        elif self.is_postgres():
            return symbol.value.replace('%s', '%%s')

    def exception_info(self, exception):
        if self.is_sqlite():
            return exception.args[0]
        elif self.is_postgres():
            return ': '.join((exception.pgcode, exception.pgerror))

    def is_sqlite(self):
        return self.settings['driver'] == "sqlite3"

    def is_postgres(self):
        return self.settings['driver'] == "psycopg2"

    def connect(self):
        if self.connection:
            return self # so that we can proxy calls to the connection.

        if self.is_sqlite():
            self.connection = DB_DRIVER.connect(os.path.join(
                self.settings['directory'],
                self.settings['database']))

        elif self.is_postgres():
            self.connection = DB_DRIVER.connect(
                database=self.settings['database'],
                user=self.settings['username'],
                password=self.settings['password'],
                port=self.settings['port'],
                host=self.settings['host'])

        return self

    def execute(self, query, params=()):
        if not self.connection:
            raise ValueError("Must connect to database before running queries.")

        if self.is_sqlite():
            return self.connection.execute(query, params)

        elif self.is_postgres():
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor

    def close(self):
        self.connection.close()
        self.connection = None

DATABASE = Database()
