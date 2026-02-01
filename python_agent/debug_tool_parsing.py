import re

def parse_tool_code(tool_code):
    print(f"Parsing: {tool_code}")
    amount_match = re.search(r"amount=['\"]?(\d+(?:\.\d+)?)['\"]?", tool_code)
    token_match = re.search(r"token=['\"](\w+)['\"]", tool_code)
    name_match = re.search(r"proposal_name=['\"](.*?)['\"]", tool_code)
    id_match = re.search(r"proposal_id=['\"](\d+)['\"]", tool_code)
    
    override_amount = float(amount_match.group(1)) if amount_match else None
    override_token = token_match.group(1) if token_match else None
    override_name = name_match.group(1) if name_match else None
    override_id = id_match.group(1) if id_match else None
    
    print(f"Result -> Name: {override_name}, ID: {override_id}, Amount: {override_amount}, Token: {override_token}")

test_cases = [
    "execute_donation(amount=22, token='USDC', proposal_name='Gaza Humanitarian Aid')",
    "execute_donation(amount=100.5, token='ETH', proposal_name='Sudan Relief')",
    "execute_donation(amount='50', token='USDT', proposal_id='5')",
]

for case in test_cases:
    parse_tool_code(case)
