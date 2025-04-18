import re

def filter_xss(comment):
    # Regular expression to search html tags.
    pattern = re.compile(r'<(script|h[1-6]|a|/a|/img|body|p|/p)>', re.IGNORECASE)
    
    # Verify if any tags were found
    if pattern.search(comment):
        return True
    else:
        return False

def format_comment(comment):

    # Manipulação de '>' e '<'
    formatted_comment = []
    inside_verde = False
    inside_vermelho = False
    buffer = []

    for char in comment:
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

    if buffer:
        formatted_comment.append(''.join(buffer))

    if inside_verde:
        formatted_comment.append('</span>')
    if inside_vermelho:
        formatted_comment.append('</span>')

    comment = ''.join(formatted_comment)

    # Manipulação de citações (>>)
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

    # Substituir links
    comment = re.sub(r'\[([^\]]+)\]\((https?://[^\s]+(?:\S)*)\)', r'<a class="hyper-link" href="\2">\1</a>', comment)

    # Manipulação de '((('
    parts = comment.split('(((')
    for index in range(1, len(parts)):
        match = re.match(r'^[^()]*\)\)\)', parts[index])
        if match:
            parts[index] = f'<span class="detected">((({match.group(0)}</span>{parts[index][len(match.group(0)):]}'
        else:
            parts[index] = f'((({parts[index]}'
    comment = ''.join(parts)

    # Manipulação de '=='
    parts = comment.split('==')
    for index in range(1, len(parts), 2):
        parts[index] = f'<span class="red-text">{parts[index]}</span>'
    comment = ''.join(parts)

    # Manipulação de '||'
    parts = comment.split('||')
    for index in range(1, len(parts), 2):
        parts[index] = f'<span class="spoiler">{parts[index]}</span>'
    comment = ''.join(parts)

    # Manipulação de [spoiler]
    comment = comment.replace('[spoiler]', '<span class="spoiler">').replace('[/spoiler]', '</span>')

    # Manipulação de [r]
    comment = comment.replace('[r]', '<span class="rainbowtext">').replace('[/r]', '</span>')

    comment = re.sub(
        r'\[wikinet\]([^\[]+)\[/wikinet\]',
        r'<a class="wikinet-hyper-link" href="https://wikinet.pro/wiki/\1" target="_blank"><span>\1</span></a>',
        comment
    )

    return comment

if __name__ == '__main__':
    print("This module should not be run directly.")