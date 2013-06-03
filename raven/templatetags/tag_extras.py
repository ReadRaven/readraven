from django import template

from raven.models import UserFeed


register = template.Library()

class FeedTagGroupNode(template.Node):

    def __init__(self, name):
        self.name = name

    def render(self, context):
        tags = [context['tag']]
        user = context['user']
        context[self.name] = UserFeed.objects.filter(tags__in=tags, user=user)
        return ''


@register.tag
def feeds_for_tag(parser, token):
    _, vocab, name = token.split_contents()
    if not vocab == 'as':
        raise Exception('Unknown assignment vocabulary')
    return FeedTagGroupNode(name)
