# Delta for Customers

**Phase:** A

## ADDED Requirements

### Requirement: Customer Billing Name And RTN Are Optional And Validated When Present

The customer's billing name (razón social, for fiscal issuance) and RTN MUST both be optional. When an RTN is present, it MUST be exactly 14 digits after stripping hyphens and spaces, with no check-digit validation in v1 (question 10: the market research suggests a 14-digit format; the verified SAR research note states none, so no check digit is enforced). An RTN that is not exactly 14 digits after stripping separators MUST be rejected with HTTP 422 and `detail: "invalid_rtn"`. Both fields are plain additions to the customer entity: they participate in the existing create/edit idempotency payload comparison and the existing tenancy scoping exactly like every other customer field, with no change to either requirement's text.

#### Scenario: An RTN with separators is accepted and normalized

- GIVEN a create or edit request with RTN `0801-1990-123456`
- WHEN the request is processed
- THEN the stored RTN is `08011990123456`

#### Scenario: An RTN with the wrong digit count is rejected

- GIVEN a create or edit request whose RTN, after stripping separators, has 13 or 15 digits
- WHEN the request is processed
- THEN the response is HTTP 422 with `detail: "invalid_rtn"`
- AND no customer is created or modified

#### Scenario: Billing name and RTN are both optional

- GIVEN a create request with no billing name and no RTN
- WHEN the request is processed
- THEN the customer is saved with neither field set

#### Scenario: Billing name and RTN are editable independently of phone

- GIVEN an active customer with no billing name or RTN
- WHEN an edit request sets only the billing name and RTN
- THEN both are updated
- AND the name, phone, and mobile/landline flag are unchanged

#### Scenario: Billing name and RTN participate in create idempotency like any other field

- GIVEN a customer was already created with client-generated id `C1`, including a billing name and RTN
- WHEN a create request reuses `C1` with the same id but a different RTN
- THEN the response is HTTP 409 with `detail: "customer_id_conflict"`
- AND the existing customer is unchanged
