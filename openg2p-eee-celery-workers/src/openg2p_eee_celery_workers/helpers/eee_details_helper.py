from sqlalchemy import text


# TODO: Implement batching in beneficiary search -- BULK INSERT with batching
def persist_eee_details(registrant_ids, pbms_request_id, eee_session):
    for registrant_id in registrant_ids:
        eee_session.execute(
            text(
                "INSERT INTO g2p_eee_details (pbms_request_id, registrant_id) VALUES (:pbms_request_id, :registrant_id)"
            ),
            {
                "pbms_request_id": pbms_request_id,
                "registrant_id": registrant_id,
            },
        )
