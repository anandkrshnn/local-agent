import re
user_input = "Search the internet for AI news"
memory_pattern = r'(?:search|find|look up|recall|show)\s+(?:memory|history)\s+(?:for\s+)?[\'"]?(.+?)[\'"]?$'
web_pattern = r'(?:search|find|look up|google)\s+(?:the\s+)?(?:web|internet|online)\s+(?:for\s+)?[\'"]?(.+?)[\'"]?$'

print(f"Memory Match: {bool(re.search(memory_pattern, user_input, re.IGNORECASE))}")
print(f"Web Match: {bool(re.search(web_pattern, user_input, re.IGNORECASE))}")
