"""Defines a decorator to ensure that requests to auth-protected endpoints are
rejected if the user is not logged in, and to populate the user field of the
request if the user bears an authentication token."""

import base64

from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login

from .oauth_client import *
from .models import Student
from .token_gen import *

ALWAYS_LOGIN = False

def user_has_student(user):
    """Returns true if the given user has a non-None student associated with
    it."""
    try:
        s = user.student
        return s is not None
    except AttributeError:
        return False

# pylint: disable=keyword-arg-before-vararg
def view_or_basicauth(view, request, test_func, realm="", *args, **kwargs):
    """
    This is a helper function used by both 'logged_in_or_basicauth' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """

    if (request.user is None or not request.user.is_authenticated() or not
            user_has_student(request.user) or ALWAYS_LOGIN):
        key = 'HTTP_AUTHORIZATION'
        if key not in request.META:
            key = 'REDIRECT_HTTP_AUTHORIZATION'
        if key not in request.META:
            key = 'HTTP_X_AUTHORIZATION'
        if key in request.META:
            auth = request.META[key].split()
            if len(auth) == 2:
                if auth[0].lower() == "basic":
                    # Basic authentication
                    uname, passwd = base64.b64decode(auth[1]).split(':')
                    user = authenticate(username=uname, password=passwd)
                elif auth[0].lower() == "bearer":
                    # The client bears a FireRoad-issued token
                    user, error = get_user_for_token(request, auth[1])
                    if error is not None:
                        return JsonResponse(error, status=401)
                    user.backend = 'django.contrib.auth.backends.ModelBackend'

                if user is not None:
                    if user.is_active:
                        login(request, user)
                        request.user = user
                        return view(request, *args, **kwargs)
        raise PermissionDenied
        #return redirect('login')
    else:
        return view(request, *args, **kwargs)


def logged_in_or_basicauth(func, realm=""):
    """
    A simple decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.

    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.

    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.

    The purpose of this is that in several django projects I have needed
    several specific views that need to support basic authentication, yet the
    web site as a whole used django's provided authentication.

    The uses for this are for urls that are access programmatically such as
    by rss feed readers, yet the view requires a user to be logged in. Many rss
    readers support supplying the authentication credentials via http basic
    auth (and they do NOT support a redirect to a form where they post a
    username/password.)

    Use is simple:

    @logged_in_or_basicauth
    def your_view:
        ...

    You can provide the name of the realm to ask for authentication within.
    """
    def wrapper(request, *args, **kwargs):
        """Takes a request and sends it through without computation if it is an
        OPTIONS request, then runs the view_or_basicauth decorator."""
        # If it's a preflight request, don't even run the view
        if request.method == 'OPTIONS':
            return HttpResponse()
        return view_or_basicauth(func, request,
                                 lambda u: u.is_authenticated(),
                                 realm, *args, **kwargs)
    return wrapper


def has_perm_or_basicauth(perm, realm=""):
    """
    This is similar to the above decorator 'logged_in_or_basicauth'
    except that it requires the logged in user to have a specific
    permission.

    Use:

    @logged_in_or_basicauth('asforums.view_forumcollection')
    def your_view:
        ...

    """
    def view_decorator(func):
        """Builds a wrapper view function."""
        def wrapper(request, *args, **kwargs):
            """The wrapper view function."""
            return view_or_basicauth(func, request,
                                     lambda u: u.has_perm(perm),
                                     realm, *args, **kwargs)
        return wrapper
    return view_decorator
