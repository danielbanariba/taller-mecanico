# WhatsApp Sharing Specification

**Phase:** 2

## Purpose

Sharing a work order's quote or status with the customer over WhatsApp, the trust mechanism most cited across the practitioner research. This is a client-side-only capability: it introduces no new API endpoint, no server-side messaging integration, and no WhatsApp Business API usage. It composes data already fetched for the order (which is tenant-scoped and offline-boundary-governed by the `work-orders` capability) into a `wa.me` link and, where supported, a native share sheet.

## Requirements

### Requirement: Sharing Is Offered Only When The Customer's Phone Is A Mobile Number

The system MUST offer the "Compartir por WhatsApp" action only when the work order's customer has a phone recorded and that phone is classified as mobile (per the `customers` capability's `is_mobile` flag). The system MUST NOT offer the action for a landline-only or phoneless customer.

#### Scenario: Mobile customer sees the share action

- GIVEN a work order whose customer has a mobile phone
- WHEN the order detail screen renders
- THEN the "Compartir por WhatsApp" action is visible and enabled

#### Scenario: Landline-only customer does not see the share action

- GIVEN a work order whose customer has only a landline phone
- WHEN the order detail screen renders
- THEN the "Compartir por WhatsApp" action is not shown

#### Scenario: Phoneless customer does not see the share action

- GIVEN a work order whose customer has no phone recorded
- WHEN the order detail screen renders
- THEN the "Compartir por WhatsApp" action is not shown

### Requirement: Sharing Opens A Prefilled wa.me Link With A Spanish Summary

The system MUST construct a `https://wa.me/504<8-digit-number>?text=<url-encoded summary>` link using the customer's normalized mobile number, with a Spanish-language summary of the order's number, vehicle, lines, and total, drawn entirely from `copy.ts`.

#### Scenario: Triggering the action opens the link with the order's data

- GIVEN a work order for a customer with mobile number `98765432`
- WHEN the user triggers "Compartir por WhatsApp"
- THEN a link to `https://wa.me/50498765432` is opened with a URL-encoded Spanish summary of that order's number, vehicle, lines, and total in the `text` parameter

### Requirement: Photos Are Shared Via The Web Share API When Supported, With A Text-Only Fallback

Where the browser supports file sharing (`typeof navigator.canShare === "function" && navigator.canShare({ files })` returns true), the system MUST let the user pick or take photos at share time and share them together with the Spanish summary through the Web Share API. Where file sharing is unsupported, the system MUST fall back to opening the text-only `wa.me` link.

#### Scenario: Photo sharing on a supporting browser

- GIVEN a browser where `navigator.canShare({ files })` returns true
- WHEN the user triggers "Compartir por WhatsApp" and selects one or more photos
- THEN the Web Share API is invoked with those photos and the Spanish summary together

#### Scenario: Fallback on a non-supporting browser

- GIVEN a browser where `navigator.canShare` is unavailable or returns false for files
- WHEN the user triggers "Compartir por WhatsApp"
- THEN the text-only `wa.me` link opens with the Spanish summary
- AND no photo-picker step is offered

### Requirement: Photos Are Never Uploaded To Or Stored By The App

The system MUST NOT upload any photo selected for sharing to the API, and MUST NOT persist it in any client-side storage (IndexedDB, the outbox, or the query cache). A photo picked for a share action MUST exist only transiently in the browser's share flow.

#### Scenario: No network request carries the photo

- GIVEN a user selects a photo during a WhatsApp share action
- WHEN the share completes or is cancelled
- THEN no HTTP request to the API was made containing that photo's bytes
- AND no IndexedDB store retains the photo afterward
