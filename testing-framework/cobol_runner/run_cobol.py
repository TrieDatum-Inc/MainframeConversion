"""
COBOL Runner for CBTRN02C Testing

This module runs the CBTRN02C program using GnuCOBOL to generate golden outputs.
GnuCOBOL is an open-source COBOL compiler that runs on Linux/Windows/Mac.

The runner:
1. Sets up environment variables for file assignments
2. Compiles the COBOL program (if not already compiled)
3. Runs the program with test input files
4. Captures output files and console output
5. Parses results for comparison

Prerequisites:
- GnuCOBOL installed (apt-get install gnucobol)
- CBTRN02C.cbl and copybooks available
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import re


@dataclass
class COBOLRunResult:
    """Result of running the COBOL program."""
    success: bool
    return_code: int
    stdout: str
    stderr: str
    transactions_processed: int
    transactions_rejected: int
    output_files: Dict[str, str]  # filename -> path
    error_message: Optional[str] = None


class COBOLRunner:
    """
    Runner for executing CBTRN02C using GnuCOBOL.
    """
    
    def __init__(
        self,
        cobol_source_dir: str,
        copybook_dir: str,
        working_dir: str
    ):
        """
        Initialize the COBOL runner.
        
        Args:
            cobol_source_dir: Directory containing COBOL source files
            copybook_dir: Directory containing copybook files
            working_dir: Directory for test execution
        """
        self.cobol_source_dir = Path(cobol_source_dir)
        self.copybook_dir = Path(copybook_dir)
        self.working_dir = Path(working_dir)
        self.executable_path = self.working_dir / "cbtrn02c"
        
        # Ensure working directory exists
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def compile_program(self, force: bool = False) -> Tuple[bool, str]:
        """
        Compile CBTRN02C using GnuCOBOL.
        
        Args:
            force: Force recompilation even if executable exists
            
        Returns:
            Tuple of (success, message)
        """
        if self.executable_path.exists() and not force:
            return True, f"Executable already exists at {self.executable_path}"
        
        source_file = self.cobol_source_dir / "CBTRN02C.cbl"
        if not source_file.exists():
            return False, f"Source file not found: {source_file}"
        
        # Compile with GnuCOBOL
        # -x: Create executable
        # -I: Include directory for copybooks
        # -std=ibm: Use IBM COBOL compatibility mode
        cmd = [
            "cobc",
            "-x",
            "-I", str(self.copybook_dir),
            "-std=ibm",
            "-o", str(self.executable_path),
            str(source_file)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, f"Compiled successfully to {self.executable_path}"
            else:
                return False, f"Compilation failed:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"
    
    def run_test(
        self,
        test_dir: str,
        timeout: int = 60
    ) -> COBOLRunResult:
        """
        Run CBTRN02C with test files.
        
        Args:
            test_dir: Directory containing test input files (cobol subdirectory)
            timeout: Maximum execution time in seconds
            
        Returns:
            COBOLRunResult with execution details
        """
        test_path = Path(test_dir)
        cobol_files_dir = test_path / "cobol"
        
        if not cobol_files_dir.exists():
            return COBOLRunResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="",
                transactions_processed=0,
                transactions_rejected=0,
                output_files={},
                error_message=f"Test directory not found: {cobol_files_dir}"
            )
        
        # Ensure program is compiled
        compile_success, compile_msg = self.compile_program()
        if not compile_success:
            return COBOLRunResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=compile_msg,
                transactions_processed=0,
                transactions_rejected=0,
                output_files={},
                error_message=f"Compilation failed: {compile_msg}"
            )
        
        # Set up environment variables for file assignments
        # GnuCOBOL uses environment variables to map SELECT...ASSIGN TO names
        env = os.environ.copy()
        env["DALYTRAN"] = str(cobol_files_dir / "DALYTRAN.dat")
        env["TRANFILE"] = str(cobol_files_dir / "TRANFILE.dat")
        env["XREFFILE"] = str(cobol_files_dir / "XREFFILE.dat")
        env["DALYREJS"] = str(cobol_files_dir / "DALYREJS.dat")
        env["ACCTFILE"] = str(cobol_files_dir / "ACCTFILE.dat")
        env["TCATBALF"] = str(cobol_files_dir / "TCATBALF.dat")
        
        # Ensure output files exist (empty)
        for output_file in ["TRANFILE.dat", "DALYREJS.dat"]:
            output_path = cobol_files_dir / output_file
            if not output_path.exists():
                output_path.touch()
        
        # Ensure TCATBALF exists (may be empty initially)
        tcatbalf_path = cobol_files_dir / "TCATBALF.dat"
        if not tcatbalf_path.exists():
            tcatbalf_path.touch()
        
        try:
            # Run the COBOL program
            result = subprocess.run(
                [str(self.executable_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=str(cobol_files_dir)
            )
            
            # Parse output for transaction counts
            transactions_processed = 0
            transactions_rejected = 0
            
            for line in result.stdout.split('\n'):
                if 'TRANSACTIONS PROCESSED' in line:
                    match = re.search(r':(\d+)', line)
                    if match:
                        transactions_processed = int(match.group(1))
                elif 'TRANSACTIONS REJECTED' in line:
                    match = re.search(r':(\d+)', line)
                    if match:
                        transactions_rejected = int(match.group(1))
            
            # Collect output files
            output_files = {}
            for filename in ["TRANFILE.dat", "DALYREJS.dat", "ACCTFILE.dat", "TCATBALF.dat"]:
                filepath = cobol_files_dir / filename
                if filepath.exists():
                    output_files[filename] = str(filepath)
            
            return COBOLRunResult(
                success=result.returncode in [0, 4],  # 4 = warnings (rejects exist)
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                transactions_processed=transactions_processed,
                transactions_rejected=transactions_rejected,
                output_files=output_files
            )
            
        except subprocess.TimeoutExpired:
            return COBOLRunResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr="",
                transactions_processed=0,
                transactions_rejected=0,
                output_files={},
                error_message="Execution timed out"
            )
        except Exception as e:
            return COBOLRunResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
                transactions_processed=0,
                transactions_rejected=0,
                output_files={},
                error_message=f"Execution error: {str(e)}"
            )
    
    def parse_transaction_output(self, tranfile_path: str) -> List[Dict]:
        """
        Parse the TRANFILE output to extract posted transactions.
        
        Args:
            tranfile_path: Path to TRANFILE.dat
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        
        if not os.path.exists(tranfile_path):
            return transactions
        
        with open(tranfile_path, 'r') as f:
            for line in f:
                if len(line.strip()) < 350:
                    continue
                    
                # Parse based on CVTRA05Y.cpy layout
                record = line.rstrip('\n')
                tran = {
                    'tran_id': record[0:16].strip(),
                    'type_cd': record[16:18].strip(),
                    'cat_cd': int(record[18:22]) if record[18:22].strip() else 0,
                    'source': record[22:32].strip(),
                    'desc': record[32:132].strip(),
                    'amount': self._parse_signed_decimal(record[132:144]),
                    'merchant_id': int(record[144:153]) if record[144:153].strip().isdigit() else 0,
                    'merchant_name': record[153:203].strip(),
                    'merchant_city': record[203:253].strip(),
                    'merchant_zip': record[253:263].strip(),
                    'card_num': record[263:279].strip(),
                    'orig_ts': record[279:305].strip(),
                    'proc_ts': record[305:331].strip(),
                }
                transactions.append(tran)
        
        return transactions
    
    def parse_reject_output(self, rejects_path: str) -> List[Dict]:
        """
        Parse the DALYREJS output to extract rejected transactions.
        
        Args:
            rejects_path: Path to DALYREJS.dat
            
        Returns:
            List of reject dictionaries
        """
        rejects = []
        
        if not os.path.exists(rejects_path):
            return rejects
        
        with open(rejects_path, 'r') as f:
            for line in f:
                if len(line.strip()) < 430:  # 350 + 80 = 430
                    continue
                
                record = line.rstrip('\n')
                # Transaction data is first 350 bytes
                # Validation trailer is next 80 bytes
                tran_data = record[0:350]
                trailer = record[350:430]
                
                reject = {
                    'tran_id': tran_data[0:16].strip(),
                    'reject_code': int(trailer[0:4]) if trailer[0:4].strip().isdigit() else 0,
                    'reject_desc': trailer[4:80].strip(),
                }
                rejects.append(reject)
        
        return rejects
    
    def parse_account_output(self, acctfile_path: str) -> List[Dict]:
        """
        Parse the ACCTFILE output to extract updated account records.
        
        Args:
            acctfile_path: Path to ACCTFILE.dat
            
        Returns:
            List of account dictionaries
        """
        accounts = []
        
        if not os.path.exists(acctfile_path):
            return accounts
        
        with open(acctfile_path, 'r') as f:
            for line in f:
                if len(line.strip()) < 300:
                    continue
                
                record = line.rstrip('\n')
                acct = {
                    'acct_id': record[0:11].strip(),
                    'active_status': record[11:12].strip(),
                    'curr_bal': self._parse_signed_decimal(record[12:25]),
                    'credit_limit': self._parse_signed_decimal(record[25:38]),
                    'cash_credit_limit': self._parse_signed_decimal(record[38:51]),
                    'open_date': record[51:61].strip(),
                    'expiration_date': record[61:71].strip(),
                    'reissue_date': record[71:81].strip(),
                    'curr_cyc_credit': self._parse_signed_decimal(record[81:94]),
                    'curr_cyc_debit': self._parse_signed_decimal(record[94:107]),
                    'addr_zip': record[107:117].strip(),
                    'group_id': record[117:127].strip(),
                }
                accounts.append(acct)
        
        return accounts
    
    def _parse_signed_decimal(self, value: str) -> Decimal:
        """Parse a signed decimal value from COBOL format."""
        value = value.strip()
        if not value:
            return Decimal("0.00")
        
        # Check for trailing sign
        if value.endswith('+'):
            return Decimal(value[:-1]) / 100
        elif value.endswith('-'):
            return -Decimal(value[:-1]) / 100
        else:
            # Try to parse as regular number
            try:
                return Decimal(value) / 100
            except:
                return Decimal("0.00")


def run_cobol_test(
    test_name: str,
    test_dir: str,
    cobol_source_dir: str = "/home/ubuntu/repos/MainframeConversion/app/cbl",
    copybook_dir: str = "/home/ubuntu/repos/MainframeConversion/app/cpy",
    working_dir: str = "/home/ubuntu/repos/MainframeConversion/testing-framework/cobol_runner"
) -> COBOLRunResult:
    """
    Convenience function to run a COBOL test.
    
    Args:
        test_name: Name of the test (for logging)
        test_dir: Directory containing test files
        cobol_source_dir: Directory containing COBOL source
        copybook_dir: Directory containing copybooks
        working_dir: Working directory for compilation
        
    Returns:
        COBOLRunResult
    """
    print(f"Running COBOL test: {test_name}")
    print(f"  Test directory: {test_dir}")
    
    runner = COBOLRunner(
        cobol_source_dir=cobol_source_dir,
        copybook_dir=copybook_dir,
        working_dir=working_dir
    )
    
    result = runner.run_test(test_dir)
    
    print(f"  Success: {result.success}")
    print(f"  Return code: {result.return_code}")
    print(f"  Transactions processed: {result.transactions_processed}")
    print(f"  Transactions rejected: {result.transactions_rejected}")
    
    if result.error_message:
        print(f"  Error: {result.error_message}")
    
    return result


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python run_cobol.py <test_directory>")
        print("Example: python run_cobol.py ../golden_datasets/TC001_VALID_TRANSACTION")
        sys.exit(1)
    
    test_dir = sys.argv[1]
    result = run_cobol_test("Manual Test", test_dir)
    
    if result.success:
        print("\n=== COBOL Output ===")
        print(result.stdout)
    else:
        print("\n=== COBOL Errors ===")
        print(result.stderr)
