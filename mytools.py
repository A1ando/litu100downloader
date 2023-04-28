import re

def wash(text, mode='strip'):
    """不同策略下的文本清洗工作"""
    text = re.sub('[#^%&*\/|:<>\"\\?\.]', '_', text.strip(), flags=re.ASCII)
    match mode:
        case 'strip': 
            return text
        case 'colon':
            return text.split('：')[-1].strip()
