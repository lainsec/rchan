import html
import re

def escape_html(s):
    return html.escape(s).replace('&gt;', '>').replace('&lt;', '<')

def escape_html_post_info(s):
    return html.escape(s)

def filter_xss(comment):
    pattern = re.compile(r'<(script|h[1-6]|a|/a|/img|body|p|/p)>', re.IGNORECASE)
    return bool(pattern.search(comment))

def format_comment(comment):
    
    code_blocks = []

    def save_code_block(match):
        code = match.group(1)
        code_blocks.append(code)
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

    comment = re.sub(r'\[code\](.*?)\[/code\]', save_code_block, comment, flags=re.DOTALL | re.IGNORECASE)

    comment = escape_html(comment)

    # >> quote
    parts = comment.split('>>')
    formatted_comment = [parts[0]]
    for part in parts[1:]:
        number = re.match(r'^\d+', part)
        if number:
            quoted_id = number.group(0)
            quote_span = f'<span class="quote-reply" data-id="{quoted_id}">&gt;&gt;{quoted_id}</span>'
            formatted_comment.append(f'{quote_span}{part[len(quoted_id):]}')
        else:
            formatted_comment.append(f'&gt;&gt;{part}')
    comment = ''.join(formatted_comment)

    # greentext > e redtext <
    formatted_comment = []
    inside_verde = False
    inside_vermelho = False
    buffer = []
    i = 0
    while i < len(comment):
        if comment.startswith('<span class="quote-reply"', i):
            if buffer:
                formatted_comment.append(''.join(buffer))
                buffer = []
            end_tag = comment.find('</span>', i) + len('</span>')
            formatted_comment.append(comment[i:end_tag])
            i = end_tag
            continue

        char = comment[i]
        if char == '>':
            if not inside_verde:
                if buffer:
                    formatted_comment.append(''.join(buffer))
                    buffer = []
                formatted_comment.append('<span class="verde">&gt;')
                inside_verde = True
            else:
                buffer.append('&gt;')
        elif char == '<':
            if not inside_vermelho:
                if buffer:
                    formatted_comment.append(''.join(buffer))
                    buffer = []
                formatted_comment.append('<span class="vermelho">&lt;')
                inside_vermelho = True
            else:
                buffer.append('&lt;')
        elif char == '\n':
            buffer.append(char)
            if inside_verde:
                formatted_comment.append(''.join(buffer))
                formatted_comment.append('</span>')
                buffer = []
                inside_verde = False
            elif inside_vermelho:
                formatted_comment.append(''.join(buffer))
                formatted_comment.append('</span>')
                buffer = []
                inside_vermelho = False
        else:
            buffer.append(char)
        i += 1

    if buffer:
        formatted_comment.append(''.join(buffer))
    if inside_verde:
        formatted_comment.append('</span>')
    if inside_vermelho:
        formatted_comment.append('</span>')

    comment = ''.join(formatted_comment)

    # citações novamente
    parts = comment.split('&gt;&gt;')
    formatted_comment = [parts[0]]
    for part in parts[1:]:
        number = re.match(r'^\d+', part)
        if number:
            quoted_id = number.group(0)
            quote_span = f'<span class="quote-reply" data-id="{quoted_id}">&gt;&gt;{quoted_id}</span>'
            formatted_comment.append(f'{quote_span}{part[len(quoted_id):]}')
        else:
            formatted_comment.append(f'&gt;&gt;{part}')
    comment = ''.join(formatted_comment)

    # links [texto](url)
    comment = re.sub(
        r'\[([^\]]+)\]\((https?://[^\s]+(?:\S)*)\)',
        r'<a class="hyper-link" href="\2">\1</a>',
        comment
    )

    # (((
    parts = comment.split('(((')
    for index in range(1, len(parts)):
        match = re.match(r'^[^()]*\)\)\)', parts[index])
        if match:
            parts[index] = f'<span class="detected">((({match.group(0)}</span>{parts[index][len(match.group(0)):]}'
        else:
            parts[index] = f'((({parts[index]}'
    comment = ''.join(parts)

    # ==texto==
    parts = comment.split('==')
    for index in range(1, len(parts), 2):
        parts[index] = f'<span class="red-text">{parts[index]}</span>'
    comment = ''.join(parts)

    # ||spoiler||
    parts = comment.split('||')
    for index in range(1, len(parts), 2):
        parts[index] = f'<span class="spoiler">{parts[index]}</span>'
    comment = ''.join(parts)

    # [spoiler] tags
    comment = comment.replace('[spoiler]', '<span class="spoiler">').replace('[/spoiler]', '</span>')

    # [r] arco-íris
    comment = comment.replace('[r]', '<span class="rainbowtext">').replace('[/r]', '</span>')

    # [wikinet] links
    comment = re.sub(
        r'\[wikinet\]([^\[]+)\[/wikinet\]',
        r'<a class="wikinet-hyper-link" href="https://wikinet.pro/wiki/\1" target="_blank"><span>\1</span></a>',
        comment
    )

    for idx, code in enumerate(code_blocks):
        escaped = html.escape(code.strip())
        lines = escaped.split('\n')
        list_items = ''.join(f'<li>{line}</li>' for line in lines)
        formatted_code = f'<span class="command-block"><ol>{list_items}</ol></span>'
        comment = comment.replace(f"__CODE_BLOCK_{idx}__", formatted_code)

    return comment

if __name__ == "__main__":
    print("This module should not be run directly.")