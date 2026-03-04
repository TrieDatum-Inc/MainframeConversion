export interface SignonResponse {
  user_id: string;
  user_type: string;
  access_token: string;
  token_type: string;
}

export interface Account {
  acct_id: number;
  active_status?: string;
  curr_bal?: number;
  credit_limit?: number;
  cash_credit_limit?: number;
  open_date?: string;
  expiration_date?: string;
  reissue_date?: string;
  curr_cyc_credit?: number;
  curr_cyc_debit?: number;
  addr_zip?: string;
  group_id?: string;
}

export interface Customer {
  cust_id: number;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  addr_line_1?: string;
  addr_line_2?: string;
  addr_line_3?: string;
  addr_state_cd?: string;
  addr_country_cd?: string;
  addr_zip?: string;
  phone_num_1?: string;
  phone_num_2?: string;
  ssn?: number;
  govt_issued_id?: string;
  dob_yyyymmdd?: string;
  eft_account_id?: string;
  pri_card_holder_ind?: string;
  fico_credit_score?: number;
}

export interface AccountDetail {
  account: Account;
  customer?: Customer;
}

export interface Card {
  card_num: string;
  acct_id: number;
  cvv_cd?: number;
  embossed_name?: string;
  expiration_date?: string;
  active_status?: string;
}

export interface CardDetail {
  card: Card;
  account?: Account;
  customer?: Customer;
}

export interface Transaction {
  tran_id: string;
  type_cd?: string;
  cat_cd?: number;
  source?: string;
  description?: string;
  amount?: number;
  merchant_id?: number;
  merchant_name?: string;
  merchant_city?: string;
  merchant_zip?: string;
  card_num: string;
  orig_ts?: string;
  proc_ts?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface ReportSubmitResponse {
  message: string;
  job_id?: string;
  report_type: string;
  start_date: string;
  end_date: string;
}

export interface BillPaymentResponse {
  message: string;
  acct_id: number;
  payment_amount: number;
  new_balance: number;
  tran_id: string;
}

export interface AuthorizationResponse {
  card_num: string;
  transaction_id?: string;
  auth_id_code: string;
  auth_resp_code: string;
  auth_resp_reason: string;
  approved_amt: number;
}

export interface PendingAuthDetail {
  id: number;
  acct_id: number;
  card_num: string;
  auth_date?: string;
  auth_time?: string;
  auth_type?: string;
  auth_id_code?: string;
  auth_resp_code?: string;
  auth_resp_reason?: string;
  transaction_amt?: number;
  approved_amt?: number;
  merchant_category_code?: string;
  merchant_id?: string;
  merchant_name?: string;
  merchant_city?: string;
  merchant_state?: string;
  merchant_zip?: string;
  transaction_id?: string;
  message_type?: string;
  message_source?: string;
  processing_code?: string;
  card_expiry_date?: string;
  pos_entry_mode?: string;
  acqr_country_code?: string;
  fraud_confirmed?: string;
  fraud_rpt_date?: string;
  match_status?: string;
  created_at?: string;
}

export interface PendingAuthSummary {
  acct_id: number;
  cust_id?: number;
  customer_name?: string;
  credit_limit?: number;
  cash_limit?: number;
  credit_balance?: number;
  cash_balance?: number;
  approved_count: number;
  approved_amount?: number;
  declined_count: number;
  declined_amount?: number;
  authorizations: PendingAuthDetail[];
  page: number;
  has_more: boolean;
}

export interface FraudToggleResponse {
  auth_detail_id: number;
  fraud_confirmed: string;
  fraud_rpt_date?: string;
  message: string;
}

export interface User {
  user_id: string;
  first_name?: string;
  last_name?: string;
  user_type: string;
}

export interface TransactionType {
  type_cd: string;
  type_description?: string;
}

export interface MessageResponse {
  message: string;
}
