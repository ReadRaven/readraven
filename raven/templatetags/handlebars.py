import os

from django import template
from django.conf import settings

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


class HandlebarsTemplateNode(template.Node):
    '''A node for loading in a handlebars template inside a script.'''

    def __init__(self, template_name, template_id):
        self.template_name = template_name
        self.template_id = template_id

    def render(self, context):
        string = []
        string.append('<script type="text/x-handlebars" id="{0}">'.format(
            self.template_id))

        for d in settings.TEMPLATE_DIRS:
            full_path = os.path.join(d, self.template_name)
            if os.path.exists(full_path):
                string.append(open(full_path).read())
                break

        string.append('</script>')
        return ''.join(string)


@register.tag
def load_handlebars_template(parser, token):
    _, name, node_id = token.contents.split(' ')
    return HandlebarsTemplateNode(name, node_id)
