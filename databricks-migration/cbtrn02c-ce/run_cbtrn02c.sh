#!/bin/bash
#
# CBTRN02C - Post Daily Transactions - Shell Script Wrapper
#
# This script runs the CBTRN02C PySpark job on Databricks Community Edition.
#
# Usage:
#   ./run_cbtrn02c.sh                           # Run with default settings
#   ./run_cbtrn02c.sh --batch-id 20260115120000 # Run with specific batch ID
#   ./run_cbtrn02c.sh --database mydb           # Use different database
#
# Prerequisites:
#   1. Databricks CLI installed and configured
#   2. Tables created using setup_tables.sql
#   3. Data loaded into carddemo.dalytran table
#
# For Databricks Community Edition:
#   - Upload cbtrn02c_job.py to your workspace
#   - Run this script locally or from a notebook using %sh
#

set -e

# Default values
DATABASE="carddemo"
BATCH_ID=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOB_SCRIPT="${SCRIPT_DIR}/cbtrn02c_job.py"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--batch-id)
            BATCH_ID="$2"
            shift 2
            ;;
        -d|--database)
            DATABASE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -b, --batch-id ID    Batch ID for this run (default: current timestamp)"
            echo "  -d, --database NAME  Database name (default: carddemo)"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                              # Run with defaults"
            echo "  $0 --batch-id 20260115120000   # Specific batch"
            echo "  $0 --database mydb             # Different database"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Generate batch ID if not provided
if [ -z "$BATCH_ID" ]; then
    BATCH_ID=$(date +%Y%m%d%H%M%S)
fi

echo "============================================================"
echo "CBTRN02C - Post Daily Transactions"
echo "============================================================"
echo "Batch ID:  $BATCH_ID"
echo "Database:  $DATABASE"
echo "Script:    $JOB_SCRIPT"
echo "Timestamp: $(date -Iseconds)"
echo "============================================================"

# Check if running in Databricks environment
if [ -n "$DATABRICKS_RUNTIME_VERSION" ]; then
    echo "Running in Databricks environment (Runtime: $DATABRICKS_RUNTIME_VERSION)"
    
    # In Databricks, use spark-submit directly
    spark-submit \
        --master local[*] \
        "$JOB_SCRIPT" \
        --batch-id "$BATCH_ID" \
        --database "$DATABASE"
    
    EXIT_CODE=$?
else
    # Check for local PySpark installation
    if command -v spark-submit &> /dev/null; then
        echo "Running with local Spark installation"
        
        spark-submit \
            --master local[*] \
            --packages io.delta:delta-spark_2.12:3.1.0 \
            --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" \
            --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
            "$JOB_SCRIPT" \
            --batch-id "$BATCH_ID" \
            --database "$DATABASE"
        
        EXIT_CODE=$?
    else
        echo "ERROR: spark-submit not found"
        echo ""
        echo "To run this script, you need either:"
        echo "  1. Databricks environment (notebook or cluster)"
        echo "  2. Local Spark installation with spark-submit in PATH"
        echo ""
        echo "For Databricks Community Edition:"
        echo "  - Upload cbtrn02c_job.py to your workspace"
        echo "  - Create a notebook and run:"
        echo "    %run /Workspace/path/to/cbtrn02c_job"
        echo ""
        exit 1
    fi
fi

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "JOB COMPLETED SUCCESSFULLY"
elif [ $EXIT_CODE -eq 4 ]; then
    echo "JOB COMPLETED WITH WARNINGS (some transactions rejected)"
else
    echo "JOB FAILED (exit code: $EXIT_CODE)"
fi
echo "============================================================"

exit $EXIT_CODE
