from openid.consumer.stores import ConsumerAssociation
from openid import oidUtil

import string

allowed_handle = []
for c in string.printable:
    if c not in string.whitespace:
        allowed_handle.append(c)
allowed_handle = ''.join(allowed_handle)

def generateHandle(n):
    return oidUtil.randomString(n, allowed_handle)

generateSecret = oidUtil.randomString

allowed_nonce = string.letters + string.digits
def generateNonce():
    return oidUtil.randomString(8, allowed_nonce)

def testStore(store):
    """Make sure a given store has a minimum of API compliance. Call
    this function with an empty store.

    Raises AssertionError if the store does not work as expected.

    OpenIDStore -> NoneType
    """

    ### Association functions

    server_url = 'http://www.myopenid.com/openid'
    secret = generateSecret(20)
    handle = generateHandle(128)

    assoc = ConsumerAssociation.fromExpiresIn(600, server_url, handle, secret)

    # Make sure that a missing association returns no result
    missing_assoc = store.getAssociation(server_url)
    assert missing_assoc is None

    # Check that after storage, getting returns the same result
    store.storeAssociation(assoc)
    retrieved_assoc = store.getAssociation(server_url)
    assert retrieved_assoc.secret == assoc.secret, (retrieved_assoc.secret,
                                                    assoc.secret)
    assert retrieved_assoc.handle == assoc.handle
    assert retrieved_assoc.server_url == assoc.server_url

    # more than once
    retrieved_assoc = store.getAssociation(server_url)
    assert retrieved_assoc.secret == assoc.secret
    assert retrieved_assoc.handle == assoc.handle
    assert retrieved_assoc.server_url == assoc.server_url

    # Storing more than once has no ill effect
    store.storeAssociation(assoc)
    retrieved_assoc = store.getAssociation(server_url)
    assert retrieved_assoc.secret == assoc.secret
    assert retrieved_assoc.handle == assoc.handle
    assert retrieved_assoc.server_url == assoc.server_url

    # Removing an association that does not exist returns not present
    present = store.removeAssociation(server_url + 'x', handle)
    assert not present

    # Removing an association that is present returns present
    present = store.removeAssociation(server_url, handle)
    assert present

    # but not present on subsequent calls
    present = store.removeAssociation(server_url, handle)
    assert not present

    # One association with server_url
    store.storeAssociation(assoc)
    handle2 = generateHandle(128)
    assoc2 = ConsumerAssociation.fromExpiresIn(
        600, server_url, handle2, secret)
    store.storeAssociation(assoc2)

    # After storing an association with a different handle, but the
    # same server_url, the most recent association is available. There
    # is no guarantee either way about the first association. (and
    # thus about the return value of removeAssociation)
    retrieved_assoc = store.getAssociation(server_url)
    assert retrieved_assoc.server_url == server_url
    assert retrieved_assoc.handle == handle2
    assert retrieved_assoc.secret == secret

    ### Nonce functions

    # Random nonce (not in store)
    nonce1 = generateNonce()

    # A nonce is not present by default
    present = store.useNonce(nonce1)
    assert not present

    # Storing once causes useNonce to return True the first, and only
    # the first, time it is called after the store.
    store.storeNonce(nonce1)
    present = store.useNonce(nonce1)
    assert present
    present = store.useNonce(nonce1)
    assert not present

    # Storing twice has the same effect as storing once.
    store.storeNonce(nonce1)
    store.storeNonce(nonce1)
    present = store.useNonce(nonce1)
    assert present
    present = store.useNonce(nonce1)
    assert not present

    ### Auth key functions

    # There is no key to start with, so generate a new key and return it.
    key = store.getAuthKey()

    # The second time around should return the same as last time.
    key2 = store.getAuthKey()
    assert key == key2
    assert len(key) == store.AUTH_KEY_LEN

def test_filestore():
    from openid.consumer import filestore
    import tempfile
    import shutil
    try:
        temp_dir = tempfile.mkdtemp()
    except AttributeError:
        import os
        temp_dir = os.tmpnam()
        os.mkdir(temp_dir)

    try:
        store = filestore.FilesystemOpenIDStore(temp_dir)
        testStore(store)
    finally:
        shutil.rmtree(temp_dir)

def test_sqlite():
    from openid.consumer import sqlstore
    try:
        from pysqlite2 import dbapi2 as sqlite
    except ImportError:
        pass
    else:
        conn = sqlite.connect(':memory:')
        store = sqlstore.SQLiteStore(conn)
        store.createTables()
        testStore(store)

def test_mysql():
    from openid.consumer import sqlstore
    try:
        import MySQLdb
    except ImportError:
        pass
    else:
        db_user = 'openid_test'
        db_passwd = ''
        db_name = 'openid_test'

        from MySQLdb.constants import ER

        # Change this connect line to use the right user and password
        conn = MySQLdb.connect(user=db_user, passwd=db_passwd)

        # Clean up from last time, if the final drop database did not work
        try:
            conn.query('DROP DATABASE %s;' % db_name)
        except conn.OperationalError, why:
            if why[0] == ER.DB_DROP_EXISTS:
                pass # It's OK that the database did not exist. We're
                     # just cleaning up from last time in case we
                     # failed to clean up at the end.
            else:
                raise

        conn.query('CREATE DATABASE %s;' % db_name)
        try:
            conn.query('USE %s;' % db_name)

            # OK, we're in the right environment. Create store and
            # create the tables.
            store = sqlstore.MySQLStore(conn)
            store.createTables()

            # At last, we get to run the test.
            testStore(store)
        finally:
            # Remove the database. If you want to do post-mortem on a
            # failing test, comment out this line.
            conn.query('DROP DATABASE %s;' % db_name)

if __name__ == '__main__':
    #test_filestore()
    test_sqlite()
    test_mysql()