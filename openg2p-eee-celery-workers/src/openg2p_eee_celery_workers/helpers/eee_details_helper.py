from sqlalchemy import text


# TODO: Implement batching in beneficiary search -- BULK INSERT with batching
def persist_eee_details(eee_details, eee_session):
    eee_session.execute(
        text(
            """
            INSERT INTO eee_details (pbms_request_id, registrant_details, entitlement_status, number_of_registrants)
            VALUES (:pbms_request_id, :registrant_details, :entitlement_status, :number_of_registrants)
            """
        ),
        eee_details,
    )
