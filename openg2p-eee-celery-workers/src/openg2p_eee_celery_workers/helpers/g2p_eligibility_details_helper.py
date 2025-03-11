from sqlalchemy import text


def persist_g2p_eligibility_details(registrant_ids, eee_request_id, eee_session):
    for registrant_id in registrant_ids:
        eee_session.execute(
            text(
                "INSERT INTO g2p_eligibility_details (eee_request_id, registrant_id) VALUES (:eee_request_id, :registrant_id)"
            ),
            {
                "eee_request_id": eee_request_id,
                "registrant_id": registrant_id,
            },
        )
