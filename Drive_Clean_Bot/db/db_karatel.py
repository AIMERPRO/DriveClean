from . import connection_raw as db_conn


def get_karatel_not_sent_washcheck():
    connection = db_conn.open_connection_karatelbot()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
            washcheck.id_user,
            washcheck.gosnomer,
            washcheck.datetime_create,
            washcheck.id
            FROM washcheck
            WHERE washcheck.sent_to_driveclean_worker = 0
            AND washcheck.complete = 1
        """)

        values_tuple = cursor.fetchall()

    finally:
        db_conn.close_connection(connection)

    return values_tuple


def get_karatel_washchecks_checklist_by_id_washcheck(id_washckeck):
    connection = db_conn.open_connection_karatelbot()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
            washcheck_checklist.id_element,
            washcheck_checklist.result
            FROM washcheck_checklist
            WHERE washcheck_checklist.id_washcheck = %s
        """, (id_washckeck,))
        values_tuple = cursor.fetchall()


    finally:
        db_conn.close_connection(connection)

    return values_tuple


def get_karatel_balls_from_element_by_id(id_element):
    connection = db_conn.open_connection_karatelbot()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
            n_washcheck_elements.score
            FROM n_washcheck_elements
            WHERE n_washcheck_elements.id = %s
        """, (id_element,))
        values_tuple = cursor.fetchall()


    finally:
        db_conn.close_connection(connection)

    return values_tuple


from . import connection_raw as db_conn


def get_karatel_not_sent_outcheck():
    connection = db_conn.open_connection_karatelbot()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
            outcheck.id_user,
            outcheck.gosnomer,
            outcheck.datetime_create,
            outcheck.id
            FROM outcheck
            WHERE outcheck.sent_to_driveclean_worker = 0
            AND outcheck.complete = 1
        """)

        values_tuple = cursor.fetchall()

    finally:
        db_conn.close_connection(connection)

    return values_tuple


def get_karatel_outcheck_checklist_by_id_outcheck(id_outcheck):
    connection = db_conn.open_connection_karatelbot()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
            outcheck_checklist.id_element,
            outcheck_checklist.result
            FROM outcheck_checklist
            WHERE outcheck_checklist.id_outcheck = %s
        """, (id_outcheck,))
        values_tuple = cursor.fetchall()


    finally:
        db_conn.close_connection(connection)

    return values_tuple


def get_karatel_outcheck_get_photos_by_id_outcheck(id_outcheck):
    connection = db_conn.open_connection_karatelbot()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
            media.file_id
            FROM media
            WHERE media.id_outcheck = %s
        """, (id_outcheck,))
        values_tuple = cursor.fetchall()


    finally:
        db_conn.close_connection(connection)

    return values_tuple


def set_karatel_outcheck_sent(id_outcheck):
    connection = db_conn.open_connection_karatelbot()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE outcheck
            SET outcheck.sent_to_driveclean_worker = 1
            WHERE outcheck.id = %s
        """, (id_outcheck,))
        connection.commit()


    finally:
        db_conn.close_connection(connection)

    return True


def set_karatel_washcheck_sent(id_washcheck):
    connection = db_conn.open_connection_karatelbot()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE washcheck
            SET washcheck.sent_to_driveclean_worker = 1
            WHERE washcheck.id = %s
        """, (id_washcheck,))
        connection.commit()


    finally:
        db_conn.close_connection(connection)

    return True