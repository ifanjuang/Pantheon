# Example — Medical Referral Letter from Consultation Notes

Status: fictional professional example — educational support only.

Doctrine status: draft under elaboration.

This medical example is a working draft intended to be refined through consultation with healthcare professionals.

It must not be treated as finalized professional doctrine, medical advice, diagnostic guidance, prescribing guidance or compliance position.

This example illustrates how Pantheon Next may frame AI-assisted preparation of a medical correspondence draft.

It does not replace the physician’s clinical judgment, legal obligations, data-security duties or professional responsibility.

## Scenario

A general practitioner needs to prepare a referral letter to a cardiologist from:

- consultation notes;
- recent lab results;
- ECG information;
- current treatment;
- relevant medical history.

The target is not autonomous diagnosis.

The target is a structured candidate letter that the physician reviews, corrects, signs and files.

## User request

```text
Prepare a referral letter to the cardiologist from my consultation notes and the latest lab results.
```

## Mission sheet — Task Contract excerpt

```text
Mission        : Referral letter — cardiology
Scope          : Patient [PSEUDO-A7], consultation [DATE-MASKED]
Allowed        : pseudonymized consultation note
                 relevant lab values
                 ECG summary
                 relevant history and treatment
Forbidden      : unrelated patient records
                 unrelated history
                 autonomous diagnosis
                 treatment recommendation beyond supplied notes
Output         : 1-page candidate referral letter
Approval       : physician review and signature required before use
Memory         : file in patient record only; no durable AI memory
```

## Data handling note

This example uses pseudonymization and minimization as teaching concepts.

Pseudonymization is not anonymization.

A patient may remain identifiable by context, dates, rare conditions or combined details.

Pantheon should therefore support several statuses:

```text
clear data
minimized data
pseudonymized data
still re-identifiable data
external sending forbidden
local processing only
```

## Evidence Pack excerpt

```text
Sources used:
- consultation note [pseudonymized]
- lab values [DATE-MASKED]
- ECG summary [DATE-MASKED]

Clinical elements preserved:
- blood pressure
- heart rate
- relevant current treatment
- symptom description supplied by physician

Missing / limits:
- no autonomous interpretation of ECG beyond supplied summary
- no diagnosis added by the model
- no treatment decision proposed by the model

Risk notes:
- candidate correspondence only
- physician must review, amend and sign
- identifying fields reinjected locally only if appropriate
```

## Candidate deliverable excerpt

```text
Dear colleague,

I am referring my patient [PSEUDO-A7], 58 years old, treated for hypertension, for cardiology review.

Reason for referral:
Intermittent palpitations reported over the last three weeks, without syncope or chest pain according to the consultation note.

Elements supplied:
- BP: 142/88 mmHg
- HR: 92/min, irregular on auscultation
- ECG summary: ventricular extrasystoles, tracing attached
- Lab values: potassium 3.9 mmol/L, TSH within normal range

Question for review:
Could you advise on diagnostic confirmation and whether Holter monitoring is indicated?

Kind regards,
Dr [NAME-MASKED]
```

## User Decision Gate

A User Decision Gate is needed if the user asks the system to:

- add a diagnosis not present in the notes;
- recommend treatment;
- send the letter automatically;
- retain identifiable health information outside the patient record.

```text
Decision required:
Keep the output as a correspondence draft
or
add professional clinical content manually
or
block external processing / sending
```

## Memory rule

No durable AI memory should be created from identifiable or re-identifiable health information.

Possible Memory Candidate only at method level:

```text
For medical correspondence drafts, require source-bounded input, pseudonymization/minimization check, physician review and no autonomous diagnosis.
```

This is method memory, not patient memory.

## Why this example matters

The useful distinction is:

```text
correspondence drafting ≠ diagnosis
pseudonymization ≠ anonymization
candidate letter ≠ signed medical document
stored patient file ≠ AI memory
```

## Professional review needed

This draft should be reviewed with healthcare professionals before being presented as a stable use-case doctrine.

Expected review points:

- medical confidentiality boundaries;
- health-data hosting and local-processing requirements;
- pseudonymization versus anonymization expectations;
- safe limits of AI-assisted correspondence drafting;
- exclusion of diagnosis and prescription decisions;
- patient-record filing and retention boundaries.
