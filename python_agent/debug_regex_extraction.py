
import re

def _extract_proposal_name_from_message(message: str) -> str:
    parts = message.split('|')
    clean_message = parts[0].strip()
    print(f"Analyzing message: '{clean_message}'")
    
    patterns = [
        r'(?:向|給)\s*([^直接\s]+(?: [^直接\s]+)*)\s*(?:直接)?(?:捐款|捐贈|捐)',
        r'donate(?:ing)?\s+(?:(?:\d+(?:\.\d+)?)\s*(?:USDC|USDT|ETH|DAI|tokens?)?\s+)?to\s+(.+)',
        r'donate\s+to\s+(.+?)(?:\s+(?:directly|now|1|usdc|usdt|eth|dai)|$)',
        r'到\s+(.+?)(?:\s+(?:直接|捐款|捐)|$|，|,)', # New: "到 [Name]"
        r'for\s+(.+?)(?:\s+(?:campaign|project)|$)',
        r'給\s*(.+?)\s*捐款',
        r'幫助\s*(.+)',
        r'^(.+?)(?:提案|project|proposal)\s*(?:我要|我想|I want|allows)', 
        r'(.*?)\s*(?:的)?幫我',
        r'向\s*(.+?)\s*(?:直接|捐)',
        r'^(.+?)(?=\s*(?:我要|我想|I want).*(?:捐|donate))',
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, clean_message, re.IGNORECASE)
        if match:
            print(f"Matched Pattern {i}: {pattern}")
            name = match.group(1).strip()
            name = re.sub(r'(?:\s|^)\d+(\.\d+)?\s*(USDC|USDT|ETH|DAI).*$', '', name, flags=re.IGNORECASE).strip()
            name = re.sub(r'\s+(directly|now|immediately)$', '', name, flags=re.IGNORECASE).strip()
            if name and len(name) > 2:
                print(f"Result: '{name}'")
                return name
    
    # Fallback to agent response
    if len(parts) > 1:
        agent_text = parts[1].strip()
        quote_match = re.search(r'[「"“](.+?)[」"”]', agent_text)
        if quote_match:
            print(f"Recovered from agent: {quote_match.group(1)}")
            return quote_match.group(1)

    print("No match found.")
    return None

test_msg = "我想在捐款2USDC到 Herat Afghanistan Earthquake ，直接捐款 | 我已經為您準備好「Herat Afghanistan Earthquake」提案的2 USDC直接捐款交易"
_extract_proposal_name_from_message(test_msg)
