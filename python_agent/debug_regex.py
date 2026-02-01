import re

def _extract_proposal_name_from_message(message: str) -> str:
    patterns = [
        r'(?:向|給)\s*([^直接\s]+(?: [^直接\s]+)*)\s*(?:直接)?(?:捐款|捐贈|捐)',
        r'donate(?:ing)?\s+(?:(?:\d+(?:\.\d+)?)\s*(?:USDC|USDT|ETH|DAI|tokens?)?\s+)?to\s+(.+)',
        r'donate\s+to\s+(.+?)(?:\s+(?:directly|now|1|usdc|usdt|eth|dai)|$)',
        r'給\s*(.+?)\s*捐款',
        r'幫助\s*(.+)',
        r'^(.+?)(?:提案|project|proposal)\s*(?:我要|我想|I want|allows)', 
        r'(.*?)\s*(?:的)?幫我',
        r'向\s*(.+?)\s*(?:直接|捐)',
        r'^(.+?)(?=\s*(?:我要|我想|I want).*(?:捐|donate))',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Remove artifacts like 1 USDC if caught at the end
            name = re.sub(r'(?:\s|^)\d+(\.\d+)?\s*(USDC|USDT|ETH|DAI).*$', '', name, flags=re.IGNORECASE).strip()
            # Remove "directly" or "now" if caught
            name = re.sub(r'\s+(directly|now|immediately)$', '', name, flags=re.IGNORECASE).strip()
            
            if name and len(name) > 2: return name
    return None

test_cases = [
    "Donate 22 USDC to Gaza Humanitarian Aid",
    "向 Gaza Humanitarian Aid 捐款 22 USDC",
    "I want to donate to Gaza Humanitarian Aid",
    "Donate to Gaza Humanitarian Aid 22 USDC",
    "Donate 100.5 USDT to Turkey Relief Fund",
    "Donateing 50 ETH to Sudan Emergency", 
    "Donate to Morocco directly"
]

for msg in test_cases:
    print(f"'{msg}' -> '{_extract_proposal_name_from_message(msg)}'")
