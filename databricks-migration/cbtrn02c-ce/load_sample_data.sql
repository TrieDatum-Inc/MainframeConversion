-- ============================================================
-- CBTRN02C - Load Sample Data for Testing
-- ============================================================
-- 
-- Run this script AFTER setup_tables.sql to load sample data.
-- This data can be used to test the CBTRN02C job.
--
-- For Databricks Community Edition:
--   1. Create a new notebook
--   2. Copy each INSERT statement into a cell
--   3. Run each cell to load the data
-- ============================================================

USE carddemo;

-- ============================================================
-- Load Sample Accounts
-- ============================================================
INSERT INTO carddemo.accounts VALUES
    ('00000000001', 'Y', 1500.75, 10000.00, 2000.00, '2020-01-15', '2027-12-31', NULL, 500.00, -200.00, '10001', 'PREMIUM', current_timestamp(), 'INITIAL'),
    ('00000000002', 'Y', 3250.50, 15000.00, 3000.00, '2019-06-20', '2028-06-30', NULL, 1000.00, -500.00, '20002', 'GOLD', current_timestamp(), 'INITIAL'),
    ('00000000003', 'N', 0.00, 5000.00, 1000.00, '2018-03-10', '2024-03-31', NULL, 0.00, 0.00, '30003', 'STANDARD', current_timestamp(), 'INITIAL'),
    ('00000000004', 'Y', 7890.25, 25000.00, 5000.00, '2021-09-01', '2029-09-30', NULL, 2500.00, -1000.00, '40004', 'PLATINUM', current_timestamp(), 'INITIAL'),
    ('00000000005', 'Y', 450.00, 3000.00, 500.00, '2022-02-14', '2030-02-28', NULL, 100.00, -50.00, '50005', 'STANDARD', current_timestamp(), 'INITIAL');

-- Verify accounts loaded
SELECT * FROM carddemo.accounts;

-- ============================================================
-- Load Sample Card Cross-References
-- ============================================================
INSERT INTO carddemo.card_xref VALUES
    ('4111111111111111', '100000001', '00000000001'),
    ('4222222222222222', '100000002', '00000000002'),
    ('4333333333333333', '100000003', '00000000003'),
    ('4444444444444444', '100000004', '00000000004'),
    ('4555555555555555', '100000005', '00000000005');

-- Verify card xrefs loaded
SELECT * FROM carddemo.card_xref;

-- ============================================================
-- Load Sample Daily Transactions
-- ============================================================
-- Batch ID: 20260115120000 (use this when running the job)
INSERT INTO carddemo.dalytran VALUES
    -- Valid transaction - will be posted
    ('TRN0000000000001', 'PR', 1001, 'POS', 'GROCERY STORE PURCHASE', -45.67, 123456789, 'WHOLE FOODS', 'NEW YORK', '10001', '4111111111111111', '2026-01-15-10.30.00.000000', NULL, '20260115120000', current_timestamp()),
    -- Valid transaction - will be posted
    ('TRN0000000000002', 'PR', 1002, 'ONLINE', 'AMAZON PURCHASE', -129.99, 987654321, 'AMAZON.COM', 'SEATTLE', '98101', '4222222222222222', '2026-01-15-11.45.00.000000', NULL, '20260115120000', current_timestamp()),
    -- Valid credit/payment - will be posted
    ('TRN0000000000003', 'CR', 2001, 'PAYMENT', 'PAYMENT RECEIVED', 500.00, 0, 'CUSTOMER PAYMENT', 'N/A', '00000', '4111111111111111', '2026-01-15-14.00.00.000000', NULL, '20260115120000', current_timestamp()),
    -- INVALID CARD - will be rejected with code 100
    ('TRN0000000000004', 'PR', 1001, 'POS', 'GAS STATION', -55.00, 111222333, 'SHELL', 'CHICAGO', '60601', '9999999999999999', '2026-01-15-09.00.00.000000', NULL, '20260115120000', current_timestamp()),
    -- EXPIRED ACCOUNT - will be rejected with code 103
    ('TRN0000000000005', 'PR', 1003, 'POS', 'ELECTRONICS', -150.00, 444555666, 'BEST BUY', 'LOS ANGELES', '90001', '4333333333333333', '2026-01-15-16.30.00.000000', NULL, '20260115120000', current_timestamp());

-- Verify daily transactions loaded
SELECT * FROM carddemo.dalytran WHERE batch_id = '20260115120000';

-- ============================================================
-- Summary
-- ============================================================
SELECT 'Accounts' as table_name, COUNT(*) as row_count FROM carddemo.accounts
UNION ALL
SELECT 'Card XRefs', COUNT(*) FROM carddemo.card_xref
UNION ALL
SELECT 'Daily Transactions', COUNT(*) FROM carddemo.dalytran;
