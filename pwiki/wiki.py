"""Classes for use by a client to interact with a MediaWiki instance's API"""
import logging
import pickle

from pathlib import Path
from typing import Union

import requests

from .ns import NS
from .oquery import OQuery
from .waction import WAction

_DEFAULT_COOKIE_JAR = Path("./pwiki.pickle")

log = logging.getLogger(__name__)


class Wiki:
    """General wiki-interfacing functionality and config data"""

    def __init__(self, domain: str = "en.wikipedia.org", username: str = None, password: str = None, cookie_jar: Path = _DEFAULT_COOKIE_JAR):
        """Initializer, creates a new Wiki object.

        Args:
            domain (str): The shorthand domain of the Wiki to target (e.g. "en.wikipedia.org")
            username (str, optional): The username to login as. Does nothing if `password` is not set.  Defaults to None.
            password (str, optional): The password to use when logging in. Does nothing if `username` is not set.  Defaults to None.
        """
        self.endpoint = f"https://{domain}/w/api.php"
        self.domain = domain
        self.client = requests.Session()

        self.username = None
        self.is_logged_in = False
        self.csrf_token = "+\\"

        self._refresh_rights()

        if not self.load_cookies(cookie_jar) and username and password:
            self.login(username, password)

        self.ns_manager = OQuery.fetch_namespaces(self)

    def __repr__(self) -> str:
        """Generate a str representation of this Wiki object.  Useful for logging.

        Returns:
            str: A str representation of this Wiki object.
        """
        return f"[{self.username or '<Anonymous>'} @ {self.domain}]"

    def _refresh_rights(self):
        """Refreshes the cached user rights fields.  If not logged in, then set the user rights to the defaults (i.e. no rights)."""
        if not self.username:
            self.rights = []
            self.is_bot = False
        else:
            self.rights = self.list_user_rights()
            self.is_bot = "bot" in self.rights

    def load_cookies(self, cookie_jar: Path = _DEFAULT_COOKIE_JAR) -> bool:
        """Load saved cookies from a file into this pwiki instance.

        Args:
            cookie_jar (Path, optional): The path to the cookies. Defaults to `_DEFAULT_COOKIE_JAR` (`./pwiki.pickle`).

        Returns:
            bool: True if successful (confirmed with server that cookies are valid).
        """
        if not cookie_jar or not cookie_jar.is_file():
            return False

        with cookie_jar.open('rb') as f:
            self.client.cookies = pickle.load(f)

        self.csrf_token = OQuery.fetch_token(self)
        if self.csrf_token == "+\\":
            log.warning("Cookies loaded from '%s' are invalid! Abort.", cookie_jar)
            self.client.cookies.clear()
            return False

        self.username = self.whoami()
        self._refresh_rights()
        self.is_logged_in = True

        return True

    def clear_cookies(self, cookie_jar: Path = _DEFAULT_COOKIE_JAR):
        """Deletes any saved cookies from disk.

        Args:
            cookie_jar (Path, optional): The local Path to the cookie jar. Defaults to _DEFAULT_COOKIE_JAR.
        """
        log.info("%s: Removing cookie jar at '%s'", self, cookie_jar)

        cookie_jar.unlink(True)

    def save_cookies(self, output_path: Path = _DEFAULT_COOKIE_JAR):
        """Write the cookies of the Wiki object to disk, so they can be used in the future.

        Args:
            output_path (Path, optional): The local path to save the cookies at.  Defaults to _DEFAULT_COOKIE_JAR (`./pwiki.pickle`).
        """
        log.info("%s: Saving cookies to '%s'", self, output_path)

        with output_path.open('wb') as f:
            pickle.dump(self.client.cookies, f)

    def which_ns(self, title: str) -> str:
        return result[0][:-1] if (result := self.ns_manager.ns_regex.match(title)) else "Main"

    def nss(self, title: str) -> str:
        return self.ns_manager.ns_regex.sub("", title, 1)

    def convert_ns(self, title: str, ns: Union[str, NS]) -> str:
        return f"{self.ns_manager.stringify(ns)}:{self.nss(title)}"

    def filter_by_ns(self, titles: list[str], *nsl: Union[str, NS]) -> list[str]:
        nsl = {self.ns_manager.stringify(ns) for ns in nsl}
        return [s for s in titles if self.which_ns(s) in nsl]

    def talk_page_of(self, title: str) -> str:
        if (ns_id := self.ns_manager.m.get(self.which_ns(title))) % 2 == 0:
            return f"{self.ns_manager.m.get(ns_id + 1)}:{self.nss(title)}"

        log.warning("%s: could not get talk page of '%s' because it is already a talk page with an id of %d", self, title, ns_id)

    def page_of(self, title: str) -> str:
        if (ns_id := self.ns_manager.m.get(self.which_ns(title))) % 2:  # == 1
            return f"{self.ns_manager.m.get(ns_id - 1)}:{self.nss(title)}"

        log.warning("%s: could not get page of '%s' because it is not a talk page and has an id of %d", self, title, ns_id)

    ##################################################################################################
    ######################################## A C T I O N S ###########################################
    ##################################################################################################

    def login(self, username: str, password: str) -> bool:
        """Attempts to login this Wiki object.  If successful, all future calls will be automatically include authentication.

        Args:
            username (str): The username to login with
            password (str): The password to login with

        Returns:
            bool: True if successful
        """
        return WAction.login(self, username, password)

    def edit(self, title: str, text: str = None, summary: str = "", prepend: str = None, append: str = None, minor: bool = False) -> bool:
        """Attempts to edit a page on the Wiki.  Can replace text or append/prepend text.

        Args:
            title (str): The title to edit.
            text (str, optional): Text to replace the current page's contents with. Mutually exclusive with `prepend`/`append`. Defaults to None.
            summary (str, optional): The edit summary to use. Defaults to "".
            prepend (str, optional): Text to prepend to the page. Mutually exclusive with `text`. Defaults to None.
            append (str, optional): Text to append to the page.  Mutually exclusive with `text`. Defaults to None.
            minor (bool, optional): Set `True` to mark this edit as minor. Defaults to False.

        Returns:
            bool: `True` if the edit was successful.
        """
        return WAction.edit(self, title, text, summary, prepend, append, minor)

    def upload(self, path: Path, title: str, desc: str = "", summary: str = "", unstash=True, max_retries=5) -> Union[bool, str]:
        """Uploads a file to the target Wiki.

        Args:
            path (Path): the local path on your computer pointing to the file to upload
            title (str): The title to upload the file to, excluding the "`File:`" namespace.
            desc (str, optional): The text to go on the file description page.  Does nothing if `unstash` is `False`. Defaults to "".
            summary (str, optional): The upload log summary to use. Does nothing if `unstash` is `False`. Defaults to "".
            unstash (bool, optional): Indicates if the file should be unstashed (published) after upload. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts in the event of an error. Defaults to 5.

        Returns:
            Union[bool, str]: 
                * `unstash=True`: returns a bool indicating if the unstash operation succeeded.
                * `unstash=False`: returns a str with the filekey
                * `None`: Error, something went wrong
        """
        return WAction.upload(self, path, title, desc, summary, unstash, max_retries)

    ##################################################################################################
    ######################################## Q U E R I E S ###########################################
    ##################################################################################################

    def list_user_rights(self, username: str = None) -> list[str]:
        """Lists user rights for the specified user.

        Args:
            username (str, optional): The user to get rights for.  Usernames must be well formed (e.g. no wacky capitalization), and must not contain the `User:` prefix.  If set to `None`, then Wiki's username will be used.  Defaults to None.

        Returns:
            list[str]: The rights for the specified user.  `None` if something went wrong.
        """
        log.info("%s: Fetching user rights for '%s'", self, u := username or self.username)
        return OQuery.list_user_rights(self, [u]).get(u) if u else []

    def uploadable_filetypes(self) -> set:
        """Queries the Wiki for all acceptable file types which may be uploaded to this Wiki.  PRECONDITION: the target Wiki permits file uploads.

        Returns:
            set: A set containing all acceptable file types as their extensions ("." prefix is included) 
        """
        log.info("%s: Fetching a list of acceptable file upload extensions.", self)
        return OQuery.uploadable_filetypes(self)

    def whoami(self) -> str:
        """Get this Wiki's username from the server.  If not logged in, then this will return your external IP address.

        Returns:
            str: If logged in, this Wiki's username.  Otherwise, the external IP address of your device.
        """
        log.info("%s: Asking the server who I am logged in as...", self)
        return OQuery.whoami(self)
