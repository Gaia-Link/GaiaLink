import re

def _extract_proposal_name_from_message(message: str) -> str:
    # UPDATED implementation matching service.py
    
    # CRITICAL: Split by '|' to ensure we only analyze the user's message
    clean_message = message.split('|')[0].strip()
    
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
        match = re.search(pattern, clean_message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name = re.sub(r'(?:\s|^)\d+(\.\d+)?\s*(USDC|USDT|ETH|DAI).*$', '', name, flags=re.IGNORECASE).strip()
            name = re.sub(r'\s+(directly|now|immediately)$', '', name, flags=re.IGNORECASE).strip()
            if name and len(name) > 2: return name
    return None

combined_text_cases = [
    "Donate 22 USDC to Gaza Humanitarian Aid | I will help you with that.",
    "Donate to Sudan Relief | OK, preparing transaction.",
    "向 Turkey Relief 捐款 | 好的",
]

for msg in combined_text_cases:
    print(f"Input: '{msg}'\nExtracted: '{_extract_proposal_name_from_message(msg)}'\n---")
