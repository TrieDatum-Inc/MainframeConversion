import re
from fastapi import Query, HTTPException, status, Path

ACCOUNT_ID_REGEX = re.compile(r"^\d{11}$")
CARD_NUM_REGEX = re.compile(r"^\d{16}$")

def validate_optional_acct_id(
    acct_id: str | None = Query(None)
) -> str | None:
    if acct_id is not None and not ACCOUNT_ID_REGEX.fullmatch(acct_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ACCOUNT MUST BE A 11 DIGIT NUMBER"
        )
    return acct_id


def validate_optional_card_num(
    card_num: str | None = Query(None)
) -> str | None:
    if card_num is not None and not CARD_NUM_REGEX.fullmatch(card_num):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CARD MUST BE A 16 DIGIT NUMBER"
        )
    return card_num

def validate_path_variable_acct_id(
    acct_id: str = Path(..., description="Account ID must be exactly 11 digits")
) -> str:
    if not ACCOUNT_ID_REGEX.fullmatch(acct_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ACCOUNT MUST BE A 11 DIGIT NUMBER"
        )
    return acct_id

def validate_path_variable_card_num(
    card_num: str = Path(..., description="Card number must be exactly 16 digits")
) -> str:
    if not CARD_NUM_REGEX.fullmatch(card_num):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CARD MUST BE A 16 DIGIT NUMBER"
        )
    return card_num

def validate_query_parma_acct_id(
    acct_id: str = Query(..., description="Account ID must be exactly 11 digits")
) -> str:
    if not ACCOUNT_ID_REGEX.fullmatch(acct_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ACCOUNT MUST BE A 11 DIGIT NUMBER"
        )
    return acct_id

def validate_query_parma_card_num(
    card_num: str = Query(..., description="Card number must be exactly 16 digits")
) -> str:
    if not CARD_NUM_REGEX.fullmatch(card_num):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CARD MUST BE A 16 DIGIT NUMBER"
        )
    return card_num    