import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Search, CreditCard, User, Building, Phone, Calendar, DollarSign, AlertCircle } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Customer {
  cust_id: string
  first_name: string
  middle_name: string | null
  last_name: string
  addr_line_1: string | null
  addr_line_2: string | null
  city: string | null
  state_cd: string | null
  country_cd: string | null
  zip_code: string | null
  phone_num_1: string | null
  phone_num_2: string | null
  ssn: string | null
  govt_issued_id: string | null
  dob: string | null
  eft_account_id: string | null
  pri_card_holder_ind: string | null
  fico_credit_score: number | null
}

interface Account {
  acct_id: string
  active_status: string
  curr_bal: number
  credit_limit: number
  cash_credit_limit: number
  open_date: string | null
  expiration_date: string | null
  reissue_date: string | null
  curr_cyc_credit: number
  curr_cyc_debit: number
  group_id: string | null
}

interface AccountViewResponse {
  account: Account
  customer: Customer
}

interface AccountSummary {
  acct_id: string
  active_status: string
  curr_bal: number
  credit_limit: number
  group_id: string | null
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return dateStr
}

function App() {
  const [accountId, setAccountId] = useState('')
  const [accountData, setAccountData] = useState<AccountViewResponse | null>(null)
  const [accounts, setAccounts] = useState<AccountSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentDate] = useState(new Date().toLocaleDateString())
  const [currentTime] = useState(new Date().toLocaleTimeString())

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/accounts`)
      if (response.ok) {
        const data = await response.json()
        setAccounts(data)
      }
    } catch (err) {
      console.error('Failed to fetch accounts list')
    }
  }

  const handleSearch = async () => {
    if (!accountId.trim()) {
      setError('Account number not provided')
      return
    }

    setLoading(true)
    setError(null)
    setAccountData(null)

    try {
      const response = await fetch(`${API_URL}/api/accounts/${accountId}`)
      if (response.ok) {
        const data = await response.json()
        setAccountData(data)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Account not found')
      }
    } catch (err) {
      setError('Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }

  const handleAccountSelect = (acctId: string) => {
    setAccountId(acctId)
    setAccountId(acctId)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-4 text-sm text-slate-400">
          <div className="flex gap-4">
            <span>Tran: <span className="text-blue-400">CAVW</span></span>
            <span>Prog: <span className="text-blue-400">COACTVWC</span></span>
          </div>
          <div className="flex gap-4">
            <span>Date: {currentDate}</span>
            <span>Time: {currentTime}</span>
          </div>
        </div>

        <Card className="bg-slate-800 border-slate-700 mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-2xl text-center text-yellow-400">
              CardDemo - Account View
            </CardTitle>
            <CardDescription className="text-center text-slate-400">
              Modern Web Application (Converted from Mainframe COBOL/CICS)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 items-end justify-center">
              <div className="flex-1 max-w-md">
                <label className="text-sm text-cyan-400 mb-1 block">Account Number:</label>
                <Input
                  type="text"
                  placeholder="Enter 11-digit account number"
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="bg-slate-700 border-slate-600 text-green-400 font-mono"
                  maxLength={11}
                />
              </div>
              <Button 
                onClick={handleSearch} 
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Search className="w-4 h-4 mr-2" />
                {loading ? 'Searching...' : 'View Account'}
              </Button>
            </div>

            {error && (
              <Alert variant="destructive" className="mt-4 bg-red-900/50 border-red-700">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {accounts.length > 0 && !accountData && (
          <Card className="bg-slate-800 border-slate-700 mb-6">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg text-cyan-400">Available Accounts (Sample Data)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {accounts.map((acc) => (
                  <div
                    key={acc.acct_id}
                    onClick={() => handleAccountSelect(acc.acct_id)}
                    className="p-3 bg-slate-700 rounded-lg cursor-pointer hover:bg-slate-600 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-green-400">{acc.acct_id}</span>
                      <Badge variant={acc.active_status === 'Y' ? 'default' : 'secondary'}>
                        {acc.active_status === 'Y' ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <div className="text-sm text-slate-400 mt-1">
                      Balance: {formatCurrency(acc.curr_bal)} | {acc.group_id}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-3">Click an account to view details</p>
            </CardContent>
          </Card>
        )}

        {accountData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2 text-cyan-400">
                  <CreditCard className="w-5 h-5" />
                  Account Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400">Account Number</label>
                    <p className="font-mono text-green-400">{accountData.account.acct_id}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Active Y/N</label>
                    <Badge variant={accountData.account.active_status === 'Y' ? 'default' : 'destructive'}>
                      {accountData.account.active_status === 'Y' ? 'Yes' : 'No'}
                    </Badge>
                  </div>
                </div>

                <Separator className="bg-slate-700" />

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> Opened
                    </label>
                    <p className="text-slate-200">{formatDate(accountData.account.open_date)}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 flex items-center gap-1">
                      <DollarSign className="w-3 h-3" /> Credit Limit
                    </label>
                    <p className="text-slate-200">{formatCurrency(accountData.account.credit_limit)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400">Expiry</label>
                    <p className="text-slate-200">{formatDate(accountData.account.expiration_date)}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Cash Credit Limit</label>
                    <p className="text-slate-200">{formatCurrency(accountData.account.cash_credit_limit)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400">Reissue</label>
                    <p className="text-slate-200">{formatDate(accountData.account.reissue_date)}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Current Balance</label>
                    <p className="text-xl font-semibold text-yellow-400">
                      {formatCurrency(accountData.account.curr_bal)}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400">Account Group</label>
                    <Badge variant="outline" className="text-cyan-400 border-cyan-400">
                      {accountData.account.group_id || '-'}
                    </Badge>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Current Cycle Credit</label>
                    <p className="text-green-400">{formatCurrency(accountData.account.curr_cyc_credit)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div></div>
                  <div>
                    <label className="text-xs text-slate-400">Current Cycle Debit</label>
                    <p className="text-red-400">{formatCurrency(accountData.account.curr_cyc_debit)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2 text-cyan-400">
                  <User className="w-5 h-5" />
                  Customer Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400">Customer ID</label>
                    <p className="font-mono text-green-400">{accountData.customer.cust_id}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">SSN</label>
                    <p className="text-slate-200">{accountData.customer.ssn || '-'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400">Date of Birth</label>
                    <p className="text-slate-200">{formatDate(accountData.customer.dob)}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">FICO Score</label>
                    <Badge 
                      variant={
                        (accountData.customer.fico_credit_score || 0) >= 750 ? 'default' :
                        (accountData.customer.fico_credit_score || 0) >= 700 ? 'secondary' : 'destructive'
                      }
                    >
                      {accountData.customer.fico_credit_score || '-'}
                    </Badge>
                  </div>
                </div>

                <Separator className="bg-slate-700" />

                <div>
                  <label className="text-xs text-slate-400">Name</label>
                  <p className="text-lg text-slate-200">
                    {accountData.customer.first_name} {accountData.customer.middle_name || ''} {accountData.customer.last_name}
                  </p>
                </div>

                <div>
                  <label className="text-xs text-slate-400 flex items-center gap-1">
                    <Building className="w-3 h-3" /> Address
                  </label>
                  <p className="text-slate-200">{accountData.customer.addr_line_1 || '-'}</p>
                  {accountData.customer.addr_line_2 && (
                    <p className="text-slate-200">{accountData.customer.addr_line_2}</p>
                  )}
                  <p className="text-slate-200">
                    {accountData.customer.city}, {accountData.customer.state_cd} {accountData.customer.zip_code}
                  </p>
                  <p className="text-slate-400">{accountData.customer.country_cd}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 flex items-center gap-1">
                      <Phone className="w-3 h-3" /> Phone 1
                    </label>
                    <p className="text-slate-200">{accountData.customer.phone_num_1 || '-'}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Phone 2</label>
                    <p className="text-slate-200">{accountData.customer.phone_num_2 || '-'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400">Government ID</label>
                    <p className="text-slate-200 text-sm">{accountData.customer.govt_issued_id || '-'}</p>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">EFT Account ID</label>
                    <p className="text-slate-200">{accountData.customer.eft_account_id || '-'}</p>
                  </div>
                </div>

                <div>
                  <label className="text-xs text-slate-400">Primary Card Holder</label>
                  <Badge variant={accountData.customer.pri_card_holder_ind === 'Y' ? 'default' : 'secondary'}>
                    {accountData.customer.pri_card_holder_ind === 'Y' ? 'Yes' : 'No'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="mt-6 text-center text-xs text-slate-500">
          <p>Modernized from COBOL/CICS Mainframe Application | Original: COACTVWC.cbl + COACTVW.bms</p>
          <p className="mt-1">Press F3 equivalent: <Button variant="ghost" size="sm" onClick={() => { setAccountData(null); setAccountId(''); setError(null); }}>Exit / Clear</Button></p>
        </div>
      </div>
    </div>
  )
}

export default App
