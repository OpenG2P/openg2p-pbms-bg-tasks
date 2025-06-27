## Order of Beat Producer Tasks

The following beat producers are imported and executed in this order. Each one is responsible for queueing background jobs for a specific stage in the eligibility and entitlement workflow.

1. **Beneficiary List Beat Producer**
   Fetches G2P beneficiary lists with a PENDING eligibility_process_status from the PBMS database. Updates their status to PROCESSING and sends tasks to the eligibility worker queue for further processing.

2. **Entitlement Beat Producer**
   Retrieves BeneficiaryListDetails with a PENDING entitlement_status and list_stage set to DISBURSEMENT from the BG Task database. Updates their status to PROCESSING and dispatches tasks to the entitlement worker queue.

3. **Disbursement Envelope Creation Beat Producer**
   Selects entitlement records that are ready for envelope creation based on specific status and stage criteria. Updates their status and queues tasks for envelope creation processing.

4. **Disbursement Batch Creation Beat Producer**
   Identifies disbursement envelopes that are ready to be grouped into batches. Updates their status and sends tasks to initiate batch creation.

5. **Disbursement Beat Producer**
   Finds disbursement batches that are ready for final disbursement actions. Updates their status and queues tasks for processing the disbursement.
