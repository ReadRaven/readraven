from urllib import urlopen


def network_available():
    '''Check to make sure the network is up.'''
    try:
        urlopen('http://www.google.com/')
        return True
    except IOError:
        return False
