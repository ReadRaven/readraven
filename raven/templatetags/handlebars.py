from django import template

register = template.Library()


class HandlebarsNode(template.Node):
    '''A node for indicating a handlebars template.'''

    def __init__(self, text):
        self.text = text

    def render(self, context):
        return self.text


@register.tag
def handlebars(parser, token):
    text = []
    while 1:
        try:
            token = parser.tokens.pop(0)
        except IndexError:
            break
        if token.contents == 'endhandlebars':
            break
        if token.token_type == template.TOKEN_VAR:
            text.append('{{')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('{%')
        text.append(token.contents)
        if token.token_type == template.TOKEN_VAR:
            text.append('}}')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('%}')
    return HandlebarsNode(''.join(text))
