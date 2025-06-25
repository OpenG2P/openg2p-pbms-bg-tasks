from sqlalchemy import text


# TODO: Implement batching in beneficiary search -- BULK INSERT with batching
def persist_beneficiary_list_details(beneficiary_list_details, eee_session):
    eee_session.execute(
        text(
            """
            INSERT INTO beneficiary_list_details (beneficiary_list_id, registrant_details, entitlement_status, number_of_registrants)
            VALUES (:beneficiary_list_id, :registrant_details, :entitlement_status, :number_of_registrants)
            """
        ),
        beneficiary_list_details,
    )
