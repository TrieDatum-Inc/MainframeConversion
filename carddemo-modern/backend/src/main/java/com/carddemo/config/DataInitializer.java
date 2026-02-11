package com.carddemo.config;

import com.carddemo.entity.*;
import com.carddemo.repository.*;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.math.BigDecimal;

@Configuration
public class DataInitializer {

    @Bean
    CommandLineRunner initData(
            UserRepository userRepository,
            AccountRepository accountRepository,
            CustomerRepository customerRepository,
            CardRepository cardRepository,
            CardXrefRepository cardXrefRepository,
            TransactionRepository transactionRepository,
            TransactionTypeRepository transactionTypeRepository,
            TransactionCategoryRepository transactionCategoryRepository,
            PasswordEncoder passwordEncoder) {

        return args -> {
            if (userRepository.count() > 0) {
                return;
            }

            User admin = new User();
            admin.setUserId("ADMIN001");
            admin.setFirstName("ADMIN");
            admin.setLastName("USER");
            admin.setPassword(passwordEncoder.encode("ADMIN001"));
            admin.setUserType("A");
            userRepository.save(admin);

            User user1 = new User();
            user1.setUserId("USER0001");
            user1.setFirstName("FIRST01");
            user1.setLastName("LAST01");
            user1.setPassword(passwordEncoder.encode("USER0001"));
            user1.setUserType("U");
            userRepository.save(user1);

            User user2 = new User();
            user2.setUserId("USER0002");
            user2.setFirstName("FIRST02");
            user2.setLastName("LAST02");
            user2.setPassword(passwordEncoder.encode("USER0002"));
            user2.setUserType("U");
            userRepository.save(user2);

            Customer cust1 = new Customer();
            cust1.setCustId("000000001");
            cust1.setFirstName("JOHN");
            cust1.setMiddleName("A");
            cust1.setLastName("DOE");
            cust1.setAddressLine1("123 MAIN ST");
            cust1.setStateCode("NY");
            cust1.setCountryCode("US");
            cust1.setZip("10001");
            cust1.setPhoneNum1("2125551234");
            cust1.setSsn("123456789");
            cust1.setDateOfBirth("1985-01-15");
            cust1.setEftAccountId("1234567890");
            cust1.setPrimaryCardHolderInd("Y");
            cust1.setFicoCreditScore(750);
            customerRepository.save(cust1);

            Customer cust2 = new Customer();
            cust2.setCustId("000000002");
            cust2.setFirstName("JANE");
            cust2.setMiddleName("B");
            cust2.setLastName("SMITH");
            cust2.setAddressLine1("456 ELM ST");
            cust2.setStateCode("CA");
            cust2.setCountryCode("US");
            cust2.setZip("90001");
            cust2.setPhoneNum1("3105559876");
            cust2.setSsn("987654321");
            cust2.setDateOfBirth("1990-06-20");
            cust2.setEftAccountId("0987654321");
            cust2.setPrimaryCardHolderInd("Y");
            cust2.setFicoCreditScore(680);
            customerRepository.save(cust2);

            Account acct1 = new Account();
            acct1.setAcctId("00000000001");
            acct1.setActiveStatus("Y");
            acct1.setCurrentBalance(new BigDecimal("1500.00"));
            acct1.setCreditLimit(new BigDecimal("5000.00"));
            acct1.setCashCreditLimit(new BigDecimal("1500.00"));
            acct1.setOpenDate("2020-01-15");
            acct1.setExpirationDate("2025-01-15");
            acct1.setCurrentCycleCredit(new BigDecimal("200.00"));
            acct1.setCurrentCycleDebit(new BigDecimal("1700.00"));
            acct1.setAddressZip("10001");
            acct1.setGroupId("GROUP001");
            accountRepository.save(acct1);

            Account acct2 = new Account();
            acct2.setAcctId("00000000002");
            acct2.setActiveStatus("Y");
            acct2.setCurrentBalance(new BigDecimal("3200.50"));
            acct2.setCreditLimit(new BigDecimal("10000.00"));
            acct2.setCashCreditLimit(new BigDecimal("3000.00"));
            acct2.setOpenDate("2019-06-01");
            acct2.setExpirationDate("2024-06-01");
            acct2.setCurrentCycleCredit(new BigDecimal("500.00"));
            acct2.setCurrentCycleDebit(new BigDecimal("3700.50"));
            acct2.setAddressZip("90001");
            acct2.setGroupId("GROUP002");
            accountRepository.save(acct2);

            Card card1 = new Card();
            card1.setCardNumber("4111111111111111");
            card1.setAccountId("00000000001");
            card1.setCvvCode("123");
            card1.setEmbossedName("JOHN A DOE");
            card1.setExpirationDate("2025-01-15");
            card1.setActiveStatus("Y");
            cardRepository.save(card1);

            Card card2 = new Card();
            card2.setCardNumber("4222222222222222");
            card2.setAccountId("00000000002");
            card2.setCvvCode("456");
            card2.setEmbossedName("JANE B SMITH");
            card2.setExpirationDate("2024-06-01");
            card2.setActiveStatus("Y");
            cardRepository.save(card2);

            CardXref xref1 = new CardXref();
            xref1.setCardNumber("4111111111111111");
            xref1.setCustomerId("000000001");
            xref1.setAccountId("00000000001");
            cardXrefRepository.save(xref1);

            CardXref xref2 = new CardXref();
            xref2.setCardNumber("4222222222222222");
            xref2.setCustomerId("000000002");
            xref2.setAccountId("00000000002");
            cardXrefRepository.save(xref2);

            TransactionType type1 = new TransactionType();
            type1.setTypeCode("01");
            type1.setTypeDescription("PURCHASE");
            transactionTypeRepository.save(type1);

            TransactionType type2 = new TransactionType();
            type2.setTypeCode("02");
            type2.setTypeDescription("PAYMENT");
            transactionTypeRepository.save(type2);

            TransactionType type3 = new TransactionType();
            type3.setTypeCode("03");
            type3.setTypeDescription("CASH ADVANCE");
            transactionTypeRepository.save(type3);

            TransactionType type4 = new TransactionType();
            type4.setTypeCode("04");
            type4.setTypeDescription("BALANCE TRANSFER");
            transactionTypeRepository.save(type4);

            TransactionType type5 = new TransactionType();
            type5.setTypeCode("05");
            type5.setTypeDescription("INTEREST");
            transactionTypeRepository.save(type5);

            TransactionCategory cat1 = new TransactionCategory();
            cat1.setTypeCode("01");
            cat1.setCategoryCode(1);
            cat1.setCategoryDescription("RETAIL PURCHASE");
            transactionCategoryRepository.save(cat1);

            TransactionCategory cat2 = new TransactionCategory();
            cat2.setTypeCode("01");
            cat2.setCategoryCode(2);
            cat2.setCategoryDescription("ONLINE PURCHASE");
            transactionCategoryRepository.save(cat2);

            TransactionCategory cat3 = new TransactionCategory();
            cat3.setTypeCode("02");
            cat3.setCategoryCode(1);
            cat3.setCategoryDescription("CHECK PAYMENT");
            transactionCategoryRepository.save(cat3);

            TransactionCategory cat4 = new TransactionCategory();
            cat4.setTypeCode("02");
            cat4.setCategoryCode(2);
            cat4.setCategoryDescription("ONLINE PAYMENT");
            transactionCategoryRepository.save(cat4);

            Transaction txn1 = new Transaction();
            txn1.setTransactionId("0000000000000001");
            txn1.setTypeCode("01");
            txn1.setCategoryCode(1);
            txn1.setSource("POS TERM");
            txn1.setDescription("WALMART PURCHASE");
            txn1.setAmount(new BigDecimal("125.50"));
            txn1.setCardNumber("4111111111111111");
            txn1.setMerchantId("000012345");
            txn1.setMerchantName("WALMART");
            txn1.setMerchantCity("NEW YORK");
            txn1.setMerchantZip("10001");
            txn1.setOriginTimestamp("2024-01-15 10:30:00.000000");
            txn1.setProcessTimestamp("2024-01-15 10:30:00.000000");
            transactionRepository.save(txn1);

            Transaction txn2 = new Transaction();
            txn2.setTransactionId("0000000000000002");
            txn2.setTypeCode("01");
            txn2.setCategoryCode(2);
            txn2.setSource("ONLINE");
            txn2.setDescription("AMAZON PURCHASE");
            txn2.setAmount(new BigDecimal("89.99"));
            txn2.setCardNumber("4111111111111111");
            txn2.setMerchantId("000067890");
            txn2.setMerchantName("AMAZON");
            txn2.setMerchantCity("SEATTLE");
            txn2.setMerchantZip("98101");
            txn2.setOriginTimestamp("2024-01-16 14:22:00.000000");
            txn2.setProcessTimestamp("2024-01-16 14:22:00.000000");
            transactionRepository.save(txn2);

            Transaction txn3 = new Transaction();
            txn3.setTransactionId("0000000000000003");
            txn3.setTypeCode("01");
            txn3.setCategoryCode(1);
            txn3.setSource("POS TERM");
            txn3.setDescription("TARGET PURCHASE");
            txn3.setAmount(new BigDecimal("250.00"));
            txn3.setCardNumber("4222222222222222");
            txn3.setMerchantId("000011111");
            txn3.setMerchantName("TARGET");
            txn3.setMerchantCity("LOS ANGELES");
            txn3.setMerchantZip("90001");
            txn3.setOriginTimestamp("2024-01-17 09:15:00.000000");
            txn3.setProcessTimestamp("2024-01-17 09:15:00.000000");
            transactionRepository.save(txn3);
        };
    }
}
