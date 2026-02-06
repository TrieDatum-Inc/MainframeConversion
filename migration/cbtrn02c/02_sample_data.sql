-- ============================================================================
-- Sample Data for CBTRN02C PySpark Migration Testing
-- Loads representative data into all Delta tables used by the batch program
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Card Cross-Reference (CCXREF / CVACT03Y)
-- ---------------------------------------------------------------------------
INSERT INTO carddemo.card_xref VALUES
    ('4111111111111111', 100000001, 80000000001),
    ('4222222222222222', 100000002, 80000000002),
    ('4333333333333333', 100000003, 80000000003),
    ('4444444444444444', 100000004, 80000000004),
    ('4555555555555555', 100000005, 80000000005);

-- ---------------------------------------------------------------------------
-- Account Master (ACCTDAT / CVACT01Y)
-- ---------------------------------------------------------------------------
INSERT INTO carddemo.account VALUES
    (80000000001, 'Y',  1500.00, 10000.00, 2000.00, '2020-01-15', '2027-12-31', '2024-01-15',  2000.00,  -500.00, '10001', 'GOLD'),
    (80000000002, 'Y',  3200.50,  5000.00, 1000.00, '2019-06-20', '2026-06-30', '2023-06-20',  3500.00,  -299.50, '20002', 'SILVER'),
    (80000000003, 'Y',  4800.00,  5000.00,  500.00, '2021-03-10', '2027-03-31', '2024-03-10',  5000.00,  -200.00, '30003', 'SILVER'),
    (80000000004, 'Y',  1000.00, 15000.00, 3000.00, '2018-11-01', '2024-11-30', '2022-11-01',  1200.00,  -200.00, '40004', 'PLATINUM'),
    (80000000005, 'Y',  2500.00,  8000.00, 1500.00, '2022-07-15', '2028-07-31', '2025-07-15',  3000.00,  -500.00, '50005', 'GOLD');

-- ---------------------------------------------------------------------------
-- Transaction Category Balance (TCATBALF / CVTRA01Y)
-- Pre-existing balances for some account/type/category combinations
-- ---------------------------------------------------------------------------
INSERT INTO carddemo.tran_cat_balance VALUES
    (80000000001, '01', 5001,  250.00),
    (80000000001, '02', 5002,  100.00),
    (80000000002, '01', 5001, 1200.00),
    (80000000003, '01', 5001,  800.00),
    (80000000005, '01', 5001,  450.00);

-- ---------------------------------------------------------------------------
-- Daily Transactions (DALYTRAN / CVTRA06Y)
-- Mix of valid and invalid transactions to exercise all validation paths
-- ---------------------------------------------------------------------------
INSERT INTO carddemo.daily_transaction VALUES
    -- Valid: normal purchase on account 80000000001
    ('TXN0000000000001', '01', 5001, 'POS',    'Grocery purchase at SuperMart',           125.50,  900000001, 'SuperMart',           'New York',      '10001', '4111111111111111', '2026-01-15-10.30.00.000000', NULL),

    -- Valid: another purchase on account 80000000002
    ('TXN0000000000002', '01', 5001, 'POS',    'Electronics at BestBuy',                  450.00,  900000002, 'BestBuy',             'Los Angeles',   '90001', '4222222222222222', '2026-01-15-11.00.00.000000', NULL),

    -- Valid: online purchase on account 80000000005
    ('TXN0000000000003', '02', 5002, 'ONLINE', 'Book purchase on Amazon',                  35.99,  900000003, 'Amazon',              'Seattle',       '98101', '4555555555555555', '2026-01-15-12.15.00.000000', NULL),

    -- Reject reason 100: card number does not exist in XREF
    ('TXN0000000000004', '01', 5001, 'POS',    'Gas station fill-up',                      55.00,  900000004, 'ShellGas',            'Chicago',       '60601', '9999999999999999', '2026-01-15-13.00.00.000000', NULL),

    -- Reject reason 102: overlimit - account 80000000003 has limit 5000, cyc_credit=5000, cyc_debit=-200, temp_bal = 5000-(-200)+500 = 5700 > 5000
    ('TXN0000000000005', '01', 5001, 'POS',    'Furniture purchase at IKEA',               500.00,  900000005, 'IKEA',               'Houston',       '77001', '4333333333333333', '2026-01-15-14.30.00.000000', NULL),

    -- Reject reason 103: expired account - account 80000000004 expired 2024-11-30, tran date 2026-01-15
    ('TXN0000000000006', '01', 5001, 'POS',    'Restaurant dinner at Olive Garden',        85.00,  900000006, 'Olive Garden',        'Dallas',        '75201', '4444444444444444', '2026-01-15-15.00.00.000000', NULL),

    -- Valid: refund (negative amount) on account 80000000001
    ('TXN0000000000007', '01', 5001, 'POS',    'Refund from SuperMart',                   -50.00,  900000001, 'SuperMart',           'New York',      '10001', '4111111111111111', '2026-01-15-16.00.00.000000', NULL),

    -- Valid: small purchase on account 80000000002
    ('TXN0000000000008', '02', 5002, 'ONLINE', 'Music subscription renewal',               9.99,  900000007, 'Spotify',             'Stockholm',     '00000', '4222222222222222', '2026-01-15-17.00.00.000000', NULL),

    -- Valid: new category combination for account 80000000005 (will INSERT into tran_cat_balance)
    ('TXN0000000000009', '03', 5003, 'ATM',    'Cash withdrawal',                         200.00,  900000008, 'Chase ATM',           'San Francisco', '94101', '4555555555555555', '2026-01-15-18.00.00.000000', NULL),

    -- Valid: purchase on account 80000000001 (third transaction for same account)
    ('TXN0000000000010', '01', 5001, 'POS',    'Coffee at Starbucks',                       5.75,  900000009, 'Starbucks',           'New York',      '10001', '4111111111111111', '2026-01-15-19.00.00.000000', NULL);

-- ---------------------------------------------------------------------------
-- Expected Results After Processing:
--
-- VALID transactions (7):
--   TXN01 -> acct 80000000001, +125.50 purchase
--   TXN02 -> acct 80000000002, +450.00 purchase
--   TXN03 -> acct 80000000005,  +35.99 online purchase
--   TXN07 -> acct 80000000001,  -50.00 refund
--   TXN08 -> acct 80000000002,   +9.99 online purchase
--   TXN09 -> acct 80000000005, +200.00 ATM withdrawal (new TCATBAL entry)
--   TXN10 -> acct 80000000001,   +5.75 purchase
--
-- REJECTED transactions (3):
--   TXN04 -> reason 100: INVALID CARD NUMBER FOUND
--   TXN05 -> reason 102: OVERLIMIT TRANSACTION
--   TXN06 -> reason 103: TRANSACTION RECEIVED AFTER ACCT EXPIRATION
--
-- Account balance updates:
--   80000000001: curr_bal += (125.50 - 50.00 + 5.75) = +81.25
--                cyc_credit += 131.25, cyc_debit += -50.00
--   80000000002: curr_bal += (450.00 + 9.99) = +459.99
--                cyc_credit += 459.99
--   80000000005: curr_bal += (35.99 + 200.00) = +235.99
--                cyc_credit += 235.99
--
-- Transaction category balance updates:
--   (80000000001, '01', 5001): +125.50 - 50.00 + 5.75 = +81.25
--   (80000000002, '01', 5001): +450.00
--   (80000000005, '02', 5002): +35.99
--   (80000000002, '02', 5002): +9.99 (new record)
--   (80000000005, '03', 5003): +200.00 (new record)
-- ---------------------------------------------------------------------------
