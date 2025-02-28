from sqlalchemy import text


def persist_g2p_eligibility_details(
    registrant_ids, g2p_que_eligibility_request_id, eee_session
):
    for registrant_id in registrant_ids:
        eee_session.execute(
            text(
                "INSERT INTO g2p_eligibility_details (eligibility_list_id, registrant_id) VALUES (:eligibility_list_id, :registrant_id)"
            ),
            {
                "eligibility_list_id": g2p_que_eligibility_request_id,
                "registrant_id": registrant_id,
            },
        )
