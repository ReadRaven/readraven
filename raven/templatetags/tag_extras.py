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


class TagUnreadCountNode(template.Node):

    def render(self, context):
        tag = context['tag']
        user = context['user']

        userfeeds = UserFeed.objects.filter(tags__in=[tag], user=user)
        unread_count = 0
        for userfeed in userfeeds:
            unread_count = unread_count + userfeed.unread_count()

        context['unread_count'] = unread_count
        return ''


@register.tag
def feeds_for_tag(parser, token):
    _, vocab, name = token.split_contents()
    if not vocab == 'as':
        raise Exception('Unknown assignment vocabulary')
    return FeedTagGroupNode(name)


@register.tag
def tag_unread_count(parser, token):
    return TagUnreadCountNode()
