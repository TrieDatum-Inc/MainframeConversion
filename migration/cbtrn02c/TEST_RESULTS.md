# CBTRN02C PySpark Migration - Test Results

**Run Date:** 2026-02-06
**Environment:** Local PySpark 3.5.4 + Delta Lake 3.2.1
**Total Tests:** 70 | **Passed:** 70 | **Failed:** 0
**Execution Time:** ~4 min 43 sec

---

## Validation Tests (`test_validation.py`)

| # | Test Case Name | Description | Expected Value | Actual Value | Status |
|---|---|---|---|---|---|
| 1 | TestReject100InvalidCard::test_card_not_in_xref_rejected | Transaction with card number not in XREF should be rejected with code 100. | `0`; `1`; `'TXN001'` _(+2 more)_ | `0`; `1`; `'TXN001'` _(+2 more)_ | PASSED |
| 2 | TestReject100InvalidCard::test_empty_xref_all_rejected | All transactions rejected when XREF table is empty. | `0`; `2`; `REJECT_INVALID_CARD for r in rejects.collect()))` | `0`; `2`; `REJECT_INVALID_CARD for r in rejects.collect()))` | PASSED |
| 3 | TestReject100InvalidCard::test_partial_card_number_match_rejected | Partial card number match should still be rejected (exact match required). | `0`; `1`; `REJECT_INVALID_CARD` | `0`; `1`; `REJECT_INVALID_CARD` | PASSED |
| 4 | TestReject101AccountNotFound::test_xref_exists_but_account_missing | Card in XREF but referenced account missing should reject with 101. | `0`; `1`; `REJECT_ACCOUNT_NOT_FOUND` _(+1 more)_ | `0`; `1`; `REJECT_ACCOUNT_NOT_FOUND` _(+1 more)_ | PASSED |
| 5 | TestReject101AccountNotFound::test_xref_points_to_wrong_account | XREF points to account ID that doesn't exist in account table. | `0`; `1`; `REJECT_ACCOUNT_NOT_FOUND` | `0`; `1`; `REJECT_ACCOUNT_NOT_FOUND` | PASSED |
| 6 | TestReject102Overlimit::test_single_transaction_exceeds_limit | Single transaction that exceeds credit limit should be rejected. | `0`; `1`; `REJECT_OVERLIMIT` | `0`; `1`; `REJECT_OVERLIMIT` | PASSED |
| 7 | TestReject102Overlimit::test_transaction_exactly_at_limit_valid | Transaction that brings balance exactly to limit should be valid. | `1`; `0` | `1`; `0` | PASSED |
| 8 | TestReject102Overlimit::test_cumulative_transactions_exceed_limit | Multiple transactions that cumulatively exceed limit - later ones rejected. | `2`; `1`; `'TXN001' in valid_ids` → True _(+3 more)_ | `2`; `1`; `True` _(+3 more)_ | PASSED |
| 9 | TestReject102Overlimit::test_negative_amount_reduces_balance | Refund (negative amount) should reduce running balance, allowing more purchases. | `3`; `0` | `3`; `0` | PASSED |
| 10 | TestReject102Overlimit::test_existing_debit_increases_available_credit | Existing cycle debit (negative) should increase available credit. | `1`; `0` | `1`; `0` | PASSED |
| 11 | TestReject103Expired::test_transaction_after_expiration_rejected | Transaction dated after account expiration should be rejected. | `0`; `1`; `REJECT_EXPIRED` | `0`; `1`; `REJECT_EXPIRED` | PASSED |
| 12 | TestReject103Expired::test_transaction_on_expiration_date_valid | Transaction on exact expiration date should be valid. | `1`; `0` | `1`; `0` | PASSED |
| 13 | TestReject103Expired::test_transaction_before_expiration_valid | Transaction before expiration date should be valid. | `1`; `0` | `1`; `0` | PASSED |
| 14 | TestValidationPriority::test_invalid_card_checked_before_account | Invalid card should be caught before account lookup. | `1`; `REJECT_INVALID_CARD` | `1`; `REJECT_INVALID_CARD` | PASSED |
| 15 | TestValidationPriority::test_overlimit_checked_before_expiration | Overlimit should be checked before expiration in validation sequence. | `1`; `REJECT_OVERLIMIT` | `1`; `REJECT_OVERLIMIT` | PASSED |

## Post Transaction Tests (`test_post_transaction.py`)

| # | Test Case Name | Description | Expected Value | Actual Value | Status |
|---|---|---|---|---|---|
| 16 | TestPostTransactions::test_single_valid_transaction_posted | A single valid transaction should appear in the transaction table. | `1`; `'TXN001'`; `Decimal('100.00')` _(+4 more)_ | `1`; `'TXN001'`; `Decimal('100.00')` _(+4 more)_ | PASSED |
| 17 | TestPostTransactions::test_multiple_valid_transactions_posted | Multiple valid transactions should all be written. | `3`; `['TXN001', 'TXN002', 'TXN003']` | `3`; `['TXN001', 'TXN002', 'TXN003']` | PASSED |
| 18 | TestPostTransactions::test_field_mapping_from_daily_to_transaction | All fields from daily transaction should be correctly mapped. | `'TXN001'`; `'02'`; `5002` _(+9 more)_ | `'TXN001'`; `'02'`; `5002` _(+9 more)_ | PASSED |
| 19 | TestPostTransactions::test_refund_transaction_posted_with_negative_amount | Negative amount (refund) should be posted correctly. | `Decimal('-150.00')` | `Decimal('-150.00')` | PASSED |
| 20 | TestPostTransactions::test_zero_amount_transaction_posted | Zero amount transaction should be posted. | `Decimal('0.00')` | `Decimal('0.00')` | PASSED |

## Account Balance Update Tests (`test_account_update.py`)

| # | Test Case Name | Description | Expected Value | Actual Value | Status |
|---|---|---|---|---|---|
| 21 | TestAccountBalanceUpdate::test_single_purchase_updates_balance | Single purchase: bal increases, cyc_credit increases, cyc_debit unchanged. | `Decimal('1250.00')`; `Decimal('1250.00')`; `Decimal('0.00')` | `Decimal('1250.00')`; `Decimal('1250.00')`; `Decimal('0.00')` | PASSED |
| 22 | TestAccountBalanceUpdate::test_refund_updates_debit | Refund (negative amount): bal decreases, cyc_debit increases, cyc_credit unchanged. | `Decimal('800.00')`; `Decimal('1000.00')`; `Decimal('-200.00')` | `Decimal('800.00')`; `Decimal('1000.00')`; `Decimal('-200.00')` | PASSED |
| 23 | TestAccountBalanceUpdate::test_multiple_purchases_same_account | Multiple purchases on same account: all aggregated in single update. | `Decimal('1350.00')`; `Decimal('1350.00')`; `Decimal('0.00')` | `Decimal('1350.00')`; `Decimal('1350.00')`; `Decimal('0.00')` | PASSED |
| 24 | TestAccountBalanceUpdate::test_mixed_purchases_and_refunds | Mix of purchases and refunds splits correctly to credit and debit. | `Decimal('1250.00')`; `Decimal('1350.00')`; `Decimal('-100.00')` | `Decimal('1250.00')`; `Decimal('1350.00')`; `Decimal('-100.00')` | PASSED |
| 25 | TestAccountBalanceUpdate::test_multiple_accounts_updated_independently | Transactions on different accounts update each independently. | `Decimal('1100.00')`; `Decimal('2500.00')` | `Decimal('1100.00')`; `Decimal('2500.00')` | PASSED |
| 26 | TestAccountBalanceUpdate::test_zero_amount_no_balance_change | Zero amount transaction should not change balances. | `Decimal('1000.00')`; `Decimal('1000.00')`; `Decimal('0.00')` | `Decimal('1000.00')`; `Decimal('1000.00')`; `Decimal('0.00')` | PASSED |
| 27 | TestAccountBalanceUpdate::test_account_without_transactions_unchanged | Account with no transactions should remain unchanged after merge. | `Decimal('5000.00')`; `Decimal('5000.00')` | `Decimal('5000.00')`; `Decimal('5000.00')` | PASSED |
| 28 | TestAccountBalanceUpdate::test_large_amount_precision | Large amount with decimal precision should be handled correctly. | `Decimal('99999999.99')` | `Decimal('99999999.99')` | PASSED |
| 29 | TestAccountBalanceUpdate::test_small_decimal_amount | Small decimal amount (0.01) should be applied correctly. | `Decimal('1000.01')` | `Decimal('1000.01')` | PASSED |

## Transaction Category Balance Tests (`test_tran_cat_balance.py`)

| # | Test Case Name | Description | Expected Value | Actual Value | Status |
|---|---|---|---|---|---|
| 30 | TestTranCatBalanceUpdate::test_new_category_balance_inserted | New (acct, type, cat) combination should INSERT a new row. | `1`; `80000000001`; `'01'` _(+2 more)_ | `1`; `80000000001`; `'01'` _(+2 more)_ | PASSED |
| 31 | TestTranCatBalanceUpdate::test_existing_category_balance_updated | Existing (acct, type, cat) combination should UPDATE the balance. | `1`; `Decimal('750.00')` | `1`; `Decimal('750.00')` | PASSED |
| 32 | TestTranCatBalanceUpdate::test_multiple_transactions_same_category | Multiple transactions with same (acct, type, cat) should aggregate. | `1`; `Decimal('800.00')` | `1`; `Decimal('800.00')` | PASSED |
| 33 | TestTranCatBalanceUpdate::test_different_categories_create_separate_rows | Different category codes on same account should create separate rows. | `2`; `Decimal('100.00')`; `Decimal('200.00')` | `2`; `Decimal('100.00')`; `Decimal('200.00')` | PASSED |
| 34 | TestTranCatBalanceUpdate::test_different_type_codes_create_separate_rows | Different type codes on same account/category should create separate rows. | `2`; `Decimal('100.00')`; `Decimal('200.00')` | `2`; `Decimal('100.00')`; `Decimal('200.00')` | PASSED |
| 35 | TestTranCatBalanceUpdate::test_mix_of_new_and_existing_categories | Some categories already exist, some are new - both handled correctly. | `2`; `Decimal('600.00')`; `Decimal('200.00')` | `2`; `Decimal('600.00')`; `Decimal('200.00')` | PASSED |
| 36 | TestTranCatBalanceUpdate::test_refund_reduces_category_balance | Negative amount (refund) should reduce the category balance. | `Decimal('350.00')` | `Decimal('350.00')` | PASSED |
| 37 | TestTranCatBalanceUpdate::test_multiple_accounts_independent_categories | Category balances for different accounts should be independent. | `2`; `Decimal('100.00')`; `Decimal('200.00')` | `2`; `Decimal('100.00')`; `Decimal('200.00')` | PASSED |
| 38 | TestTranCatBalanceUpdate::test_existing_unrelated_categories_preserved | Pre-existing category balances not touched by transactions should remain. | `2`; `Decimal('600.00')`; `Decimal('999.00')` | `2`; `Decimal('600.00')`; `Decimal('999.00')` | PASSED |

## Write Rejects Tests (`test_write_rejects.py`)

| # | Test Case Name | Description | Expected Value | Actual Value | Status |
|---|---|---|---|---|---|
| 39 | TestWriteRejects::test_invalid_card_reject_written | Reject for invalid card should be written with code 100. | `1`; `'TXN001'`; `REJECT_INVALID_CARD` _(+2 more)_ | `1`; `'TXN001'`; `REJECT_INVALID_CARD` _(+2 more)_ | PASSED |
| 40 | TestWriteRejects::test_account_not_found_reject_written | Reject for account not found should be written with code 101. | `1`; `REJECT_ACCOUNT_NOT_FOUND` | `1`; `REJECT_ACCOUNT_NOT_FOUND` | PASSED |
| 41 | TestWriteRejects::test_overlimit_reject_written | Reject for overlimit should be written with code 102. | `1`; `REJECT_OVERLIMIT`; `'OVERLIMIT' in row['reject_reason_desc']` → True | `1`; `REJECT_OVERLIMIT`; `True` | PASSED |
| 42 | TestWriteRejects::test_expired_reject_written | Reject for expired account should be written with code 103. | `1`; `REJECT_EXPIRED`; `'EXPIRATION' in row['reject_reason_desc']` → True | `1`; `REJECT_EXPIRED`; `True` | PASSED |
| 43 | TestWriteRejects::test_multiple_rejects_all_written | Multiple rejects from different validation rules all written. | `3`; `REJECT_INVALID_CARD in codes` → True; `REJECT_OVERLIMIT in codes` → True _(+1 more)_ | `3`; `True`; `True` _(+1 more)_ | PASSED |
| 44 | TestWriteRejects::test_reject_preserves_original_transaction_data | All original daily transaction fields should be preserved in reject record. | `'TXN001'`; `'02'`; `5002` _(+9 more)_ | `'TXN001'`; `'02'`; `5002` _(+9 more)_ | PASSED |
| 45 | TestWriteRejects::test_reject_timestamp_populated | Reject records should have a non-null reject_timestamp. | `not None` | `not None` | PASSED |
| 46 | TestWriteRejects::test_no_rejects_writes_nothing | When all transactions are valid, no rejects should be written. | `0` | `0` | PASSED |

## End-to-End Integration Tests (`test_end_to_end.py`)

| # | Test Case Name | Description | Expected Value | Actual Value | Status |
|---|---|---|---|---|---|
| 47 | TestEndToEndAllValid::test_single_valid_transaction_full_flow | Single valid transaction updates all output tables correctly. | `1`; `0`; `1` _(+7 more)_ | `1`; `0`; `1` _(+7 more)_ | PASSED |
| 48 | TestEndToEndAllValid::test_multiple_accounts_full_flow | Transactions across multiple accounts all processed correctly. | `3`; `3`; `Decimal('600.00')` _(+4 more)_ | `3`; `3`; `Decimal('600.00')` _(+4 more)_ | PASSED |
| 49 | TestEndToEndAllRejected::test_all_invalid_cards | All transactions with invalid cards: nothing posted, all rejected. | `0`; `2`; `0` _(+2 more)_ | `0`; `2`; `0` _(+2 more)_ | PASSED |
| 50 | TestEndToEndMixed::test_mixed_valid_and_rejected | Mix of valid, invalid-card, overlimit, and expired transactions. | `2`; `2`; `2` _(+7 more)_ | `2`; `2`; `2` _(+7 more)_ | PASSED |
| 51 | TestEndToEndMixed::test_sample_data_scenario | Replicate the scenario from 02_sample_data.sql for regression testing. | `8`; `2`; `8` _(+7 more)_ | `8`; `2`; `8` _(+7 more)_ | PASSED |
| 52 | TestEndToEndWithPreExistingData::test_updates_existing_and_inserts_new_categories | Pipeline should update existing category balances and insert new ones. | `2`; `Decimal('600.00')`; `Decimal('200.00')` | `2`; `Decimal('600.00')`; `Decimal('200.00')` | PASSED |
| 53 | TestEndToEndEmptyInput::test_no_daily_transactions | Empty daily transaction input should produce no output changes. | `0`; `0`; `Decimal('1000.00')` | `0`; `0`; `Decimal('1000.00')` | PASSED |

## Edge Case Tests (`test_edge_cases.py`)

| # | Test Case Name | Description | Expected Value | Actual Value | Status |
|---|---|---|---|---|---|
| 54 | TestBoundaryAmounts::test_one_cent_transaction | Smallest meaningful amount (0.01) should process correctly. | `1`; `0` | `1`; `0` | PASSED |
| 55 | TestBoundaryAmounts::test_zero_credit_limit_all_positive_rejected | Zero credit limit should reject any positive transaction. | `0`; `1`; `REJECT_OVERLIMIT` | `0`; `1`; `REJECT_OVERLIMIT` | PASSED |
| 56 | TestBoundaryAmounts::test_exact_credit_limit_boundary | Transaction that brings balance exactly to credit limit should be valid. | `1`; `0` | `1`; `0` | PASSED |
| 57 | TestBoundaryAmounts::test_one_cent_over_limit_rejected | One cent over credit limit should be rejected. | `0`; `1`; `REJECT_OVERLIMIT` | `0`; `1`; `REJECT_OVERLIMIT` | PASSED |
| 58 | TestBoundaryDates::test_expiration_date_exactly_one_day_after_transaction | Account expiring one day after transaction should be valid. | `1`; `0` | `1`; `0` | PASSED |
| 59 | TestBoundaryDates::test_expiration_date_one_day_before_transaction | Account expired one day before transaction should be rejected. | `0`; `1`; `REJECT_EXPIRED` | `0`; `1`; `REJECT_EXPIRED` | PASSED |
| 60 | TestBoundaryDates::test_year_end_boundary | Transaction on Dec 31 with expiration Dec 31 should be valid. | `1`; `0` | `1`; `0` | PASSED |
| 61 | TestBoundaryDates::test_jan1_after_dec31_expiration | Transaction on Jan 1 with Dec 31 expiration should be rejected. | `0`; `1`; `REJECT_EXPIRED` | `0`; `1`; `REJECT_EXPIRED` | PASSED |
| 62 | TestMultipleCardsPerAccount::test_two_cards_same_account_both_valid | Two different cards on the same account should both be processed. | `2`; `0` | `2`; `0` | PASSED |
| 63 | TestMultipleCardsPerAccount::test_two_cards_same_account_cumulative_overlimit | Two cards on same account: cumulative amount exceeds limit. | `1`; `1`; `'TXN001'` _(+2 more)_ | `1`; `1`; `'TXN001'` _(+2 more)_ | PASSED |
| 64 | TestHighVolumeProcessing::test_fifty_valid_transactions | 50 valid transactions should all be processed correctly. | `50`; `0` | `50`; `0` | PASSED |
| 65 | TestHighVolumeProcessing::test_ten_accounts_ten_transactions_each | 10 accounts with 10 transactions each should all be processed. | `100`; `0` | `100`; `0` | PASSED |
| 66 | TestTransactionTypesAndCategories::test_all_standard_type_codes | Multiple transaction type codes should all be accepted. | `3`; `0` | `3`; `0` | PASSED |
| 67 | TestTransactionTypesAndCategories::test_different_category_codes_tracked_separately | Different category codes should create separate tran_cat_balance rows. | `3`; `Decimal('100.00')`; `Decimal('200.00')` _(+1 more)_ | `3`; `Decimal('100.00')`; `Decimal('200.00')` _(+1 more)_ | PASSED |
| 68 | TestNullAndMissingFields::test_null_optional_fields_accepted | Transactions with null optional fields should still be valid. | `1`; `0` | `1`; `0` | PASSED |
| 69 | TestNullAndMissingFields::test_null_merchant_fields_posted | Null merchant fields should be preserved when posting. | `row['tran_merchant_id'] is None`; `row['tran_merchant_name'] is None`; `row['tran_merchant_city'] is None` _(+1 more)_ | `True`; `True`; `True` _(+1 more)_ | PASSED |
| 70 | TestDuplicateTransactionIds::test_duplicate_tran_ids_both_processed | Duplicate transaction IDs in input should both be processed (no dedup). | `2`; `0` | `2`; `0` | PASSED |

---

## Summary by Module

| Module | Test Count | Passed | Failed |
|---|---|---|---|
| test_validation.py | 15 | 15 | 0 |
| test_post_transaction.py | 5 | 5 | 0 |
| test_account_update.py | 9 | 9 | 0 |
| test_tran_cat_balance.py | 9 | 9 | 0 |
| test_write_rejects.py | 8 | 8 | 0 |
| test_end_to_end.py | 7 | 7 | 0 |
| test_edge_cases.py | 17 | 17 | 0 |
| **Total** | **70** | **70** | **0** |
