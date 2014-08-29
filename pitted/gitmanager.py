#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Ryan Brown <sb@ryansb.com>
#
# This file is part of pitted.
#
# pitted is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import dulwich.porcelain as git
from dulwich.errors import NotGitRepository

from IPython.utils.traitlets import Bool, Unicode
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager

import os
from os import getcwd


class PittedConfigurationException(Exception):
    pass


class GitNotebookManager(NotebookManager):
    """Git-backed storage of ipython notebooks.
    """

    notebook_dir = Unicode(getcwd(), config=True)
    repo_dir = Unicode('', config=True)

    _repo = None

    def __init__(self, **kwargs):
        super(GitNotebookManager, self).__init__(**kwargs)

        if self.repo_dir == '':
            self.repo_dir = self.notebook_dir
        elif not self.notebook_dir.startswith(self.repo_dir):
            raise PittedConfigurationException(
                "notebook_dir needs to be either the same directory or "
                "a subdirectory of repo_dir. {repo} does not contain {nb}"
                "".format(repo=self.repo_dir, nb=self.notebook_dir))

    def _check_repo(self):
        if self._repo is not None:
            return
        try:
            self._repo = Repo(self.repo_dir)
        except NotGitRepository:
            self._repo = Repo.init(self.repo_dir)
            self.log.info("hey there", self._repo.refs['refs/heads/master'])

    def path_exists(self, path):
        """Does the API-style path (directory) actually exist?

        Override this method in subclasses.

        Parameters
        ----------
        path : string
            The path to check

        Returns
        -------
        exists : bool
            Whether the path does indeed exist.
        """
        self._check_repo()
        if path == "":
            return True
        p = os.path.join('../' + path)  # dulwich thinks of ".git" as its cwd.
        self.log.info("Checking for item %s" % p)
        f = self._repo.get_named_file(p)
        if f is None:
            return False
        f.close()
        return True

    def list_dirs(self, path):
        self._check_repo()
        """List the directory models for a given API style path."""
        idx = list(self._repo.open_index())
        self.log.info("Listing dirs: %s", idx)
        # TODO: return only items in the notebook_dir of the repo
        return idx

    def list_notebooks(self, path=''):
        """Return a list of notebook dicts without content.

        This returns a list of dicts, each of the form::

            dict(notebook_id=notebook,name=name)

        This list of dicts should be sorted by name::

            data = sorted(data, key=lambda item: item['name'])
        """

        nb = filter(str.endswith(self.filename_ext), self.list_dirs(path))
        raise NotImplementedError('must be implemented in a subclass')

    def notebook_exists(self, name, path=''):
        """Returns a True if the notebook exists. Else, returns False.

        Parameters
        ----------
        name : string
            The name of the notebook you are checking.
        path : string
            The relative path to the notebook (with '/' as separator)

        Returns
        -------
        bool
        """
        self.log.info("notebook_exists looking for %s", name +
                      self.filename_ext)
        return name + self.filename_ext in self.list_dirs(path)

    def is_hidden(self, path):
        """Does the API style path correspond to a hidden directory or file?

        Parameters
        ----------
        path : string
            The path to check. This is an API path (`/` separated,
            relative to base notebook-dir).

        Returns
        -------
        exists : bool
            Whether the path is hidden.

        """
        return False  # We don't support hidden files.
