.. -*- coding: utf-8 -*-
.. \||<-snip->|| start
.. Copyright (C) 2012, Wolfgang Scherer, <Wolfgang.Scherer at gmx.de>
.. Sponsored by WIEDENMANN SEILE GMBH, http://www.wiedenmannseile.de
..
.. This file is part of Wiedenmann Utilities.
..
.. Permission is granted to copy, distribute and/or modify this document
.. under the terms of the GNU Free Documentation License, Version 1.3
.. or any later version published by the Free Software Foundation;
.. with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.
.. A copy of the license is included in the main documentation of Wiedenmann Utilities.

.. inline comments (with ws_docutils)
.. role:: rem(span)
   :format: ''
.. role:: html(span)
   :format: html
   :raw:

########################################################
:rem:`|||:sec:|||`\ BSON `Context` Extension for PyMongo
########################################################
.. \||<-snap->|| skip

:Author: `Wolfgang Scherer`_

.. contents::
.. \||<-snap->|| skip
.. \||<-snap->|| include ^index-header.snip$

Provides application specific C extension (de-)activation and a full
vertical BSON context for encoding objects.

.. warning:: This is an expert module, which does not protect against
   uninformed mistakes. Although it won't corrupt your database, you
   should still consider carefully whether you need any of the
   features.

==================================================
:rem:`|||:sec:|||`\ Rationale
==================================================

Currently, the C extensions for PyMongo/BSON can only be
enabled/disabled with site-wide installation options.

If the C extensions must be disabled (for e.g. mod_wsgi) virtual_env
has to be used, if the standard installation should not be modified.

SON manipulators can be used to automate object conversion, when
writing into a MongoDB database.  However, SON manipulators only work
in the database layer of PyMongo and require copying the entire
document tree, if the original has to be preserved.

When the :mod:`bson` module is used as a standalone serialization
protocol, you are out of luck. Since there is currently no provision
in the BSON encoder to allow graceful recovery on a per-element basis.

Writing both a SON manipulator and a document expander is redundant,
since they basically perform the same task.

==================================================
:rem:`|||:sec:|||`\ Caveat
==================================================

This extension works on the BSON encoding/decoding level.

It is perfectly possible to postpone object conversion to that stage.
This will, however, make SON manipulators for outgoing transformations
on unexpanded objects effectively defunct.

Currently there is only one SON manipulator active, namely
:class:`pymongo.son_manipulator.ObjectIdInjector`, which provides an
object ID for a document if necessary.

This manipulator only requires the top level document to be expanded
and will therefore work as expected.

==================================================
:rem:`|||:sec:|||`\ Implementation
==================================================

A BSON context :class:`bson.context.Context` is introduced, which
allows to specify encoding/decoding parameters.

This context is realized as application-wide default (global) context
and (if :func:`bson.enable_threading` is used) as thread local
context.

Unlocked context management is provided by :func:`bson.get_context`
and :func:`bson.set_context`.

Context locking is provided by :func:`bson.lock` and
:func:`bson.unlock`.

==========================================================
:rem:`|||:sec:|||`\ PyMongo/BSON Context Extension Patcher
==========================================================

- Copy pymongo_context.py
- Copy bson/context.py to bson_context.py
- import pymongo_context
- See waste_of_time.py for an example.

==================================================
:rem:`|||:sec:|||`\ TBD
==================================================

One of the parameters is an object encoding hook that allows the user
to deliver encodable data on a per-object basis.

The callback is modeled after the :func:`json.default` API.  Other
options are object methods `__bson__`, `__getstate__`, `__dict__` as
provided by :mod:`pickle`, etc.

Passing a `BSON context` hook through the database layer allows fine
tuning the BSON encoder for both database access and standalone
serialization per transaction instead of fixed application wide
settings.

.. ==================================================
.. :rem:`|||:sec:|||`\ Footnotes
.. ==================================================

:html:`<hr>`

.. \[#]

.. ==================================================
.. :rem:`|||:sec:|||`\ References
.. ==================================================

.. \||<-snap->|| include ^index-footer.snip$

:rem:`|||:sec:|||`\ **Copyright**

Copyright (C) 2012, Wolfgang Scherer, <sw@wiedenmann-seile.de>.
Sponsored by `Wiedenmann-Seile GmbH`_.
See the document source for conditions of use under the GNU Free
Documentation License.

.. _`Wiedenmann-Seile GmbH`: http://www.wiedenmannseile.de
.. _`Wolfgang Scherer`: sw@wiedenmann-seile.de

.. \||<-snip->|| stop

.. ==================================================
.. :rem:`|||:sec:|||`\ END
.. ==================================================
.. 
.. :ide-menu: Emacs IDE Main Menu - Buffer @BUFFER@
.. . M-x `eIDE-menu' ()(eIDE-menu "z")

.. :ide: DELIM: SNIPPETS (ABOUT)       |q|<- SYM ->||,   ||<- SYM ->||,  @| SYM @
.. . (let nil (symbol-tag-normalize-delimiter (cons (cons nil "||<-") (cons "->||" nil)) t) (symbol-tag-switch-delimiter-sets) (symbol-tag-normalize-delimiter (cons (cons nil "||<-") (cons "->||" nil)) t) (setq symbol-tag-match-rx "sn[i]p") (setq symbol-tag-enclose-delimiter-set (symbol-tag-normalize-delimiter (cons (cons nil "@|") (cons "@" nil)))))

.. :ide: DELIM: SNIPPETS (DOC)          ||<- SYM ->||,     |: SYM :|,     ` SYM `
.. . (let nil (symbol-tag-normalize-delimiter (cons (cons nil "|:") (cons ":|" nil)) t) (symbol-tag-switch-delimiter-sets) (symbol-tag-normalize-delimiter (cons (cons nil "||<-") (cons "->||" nil)) t) (setq symbol-tag-match-rx "sn[i]p") (setq symbol-tag-enclose-delimiter-set (symbol-tag-normalize-delimiter (cons (cons "\\(\\`\\|[^\\]\\)" "`") (cons "`" nil)))))

.. :ide: DELIM: SNIPPETS (SNIP DOC)     ||<- SYM ->||,     |: SYM :|,     @ SYM @
.. . (let nil (symbol-tag-normalize-delimiter (cons (cons nil "|:") (cons ":|" nil)) t) (symbol-tag-switch-delimiter-sets) (symbol-tag-normalize-delimiter (cons (cons nil "||<-") (cons "->||" nil)) t) (setq symbol-tag-match-rx "sn[i]p") (setq symbol-tag-enclose-delimiter-set (symbol-tag-normalize-delimiter (cons (cons nil "@") (cons "@" nil)))))

.. :ide: DELIM: SNIPPETS (FILLME)       ||<- SYM ->||,     :: SYM ::,     @ SYM @
.. . (let nil (symbol-tag-normalize-delimiter (cons (cons nil "::") (cons "::" nil)) t) (symbol-tag-switch-delimiter-sets) (symbol-tag-normalize-delimiter (cons (cons nil "||<-") (cons "->||" nil)) t) (setq symbol-tag-match-rx "sn[i]p") (setq symbol-tag-enclose-delimiter-set (symbol-tag-normalize-delimiter (cons (cons nil "@") (cons "@" nil)))))

.. :ide: DELIM: SNIPPETS (SUBST)        ||<- SYM ->||,      @ SYM @,      @ SYM @
.. . (let nil (symbol-tag-normalize-delimiter (cons (cons nil "@") (cons "@" nil)) t) (symbol-tag-switch-delimiter-sets) (symbol-tag-normalize-delimiter (cons (cons nil "||<-") (cons "->||" nil)) t) (setq symbol-tag-match-rx "sn[i]p") (setq symbol-tag-enclose-delimiter-set (symbol-tag-normalize-delimiter (cons (cons "[^\\]" "`") (cons "`" nil)))))

.. :ide: +#-
.. . Snippet Delimiter Sets ()

.. :ide: DELIM: ReST (links)              ` SYM `_,    .. _` SYM `,      ` SYM `
.. . (let nil (symbol-tag-normalize-delimiter (cons (cons "[^\\]" "`") (cons "`_" nil)) t) (symbol-tag-switch-delimiter-sets) (symbol-tag-normalize-delimiter (cons (cons nil ".. _`") (cons "`:" nil)) t) (setq symbol-tag-enclose-delimiter-set (symbol-tag-normalize-delimiter (cons (cons "\\(\\`\\|[^\\]\\)" "`") (cons "`" nil)))))

.. :ide: DELIM: STANDARD (GNU quoting)    |: SYM :|,       :: SYM ::,     ` SYM '
.. . (let nil (symbol-tag-normalize-delimiter (cons (cons nil "::") (cons "::" nil)) t) (symbol-tag-switch-delimiter-sets) (symbol-tag-normalize-delimiter (cons (cons nil "|:") (cons ":|" nil)) t) (setq symbol-tag-enclose-delimiter-set (symbol-tag-normalize-delimiter (cons (cons nil "`") (cons "'" nil)))))

.. :ide: DELIM: STANDARD (ReST quoting)   |: SYM :|,       :: SYM ::,     ` SYM `
.. . (let nil (symbol-tag-normalize-delimiter (cons (cons nil "::") (cons "::" nil)) t) (symbol-tag-switch-delimiter-sets) (symbol-tag-normalize-delimiter (cons (cons nil "|:") (cons ":|" nil)) t) (setq symbol-tag-enclose-delimiter-set (symbol-tag-normalize-delimiter (cons (cons "[^\\]" "`") (cons "`" nil)))))

.. :ide: +#-
.. . Delimiter Sets ()

.. :ide: COMPILE: render reST as LaTeX
.. . (let* ((fp (buffer-file-name)) (fn (file-name-nondirectory fp))) (save-match-data (if (string-match-t "[.][^.]*$" fn) (setq fn (replace-match "" nil t fn)))) (let ((args (concat " " fp " | ws_rst2latex.py --traceback | tee " fn ".tex"))) (save-buffer) (compile (concat "PATH=\".:$PATH\"; cat " args))))

.. :ide: COMPILE: render reST as MAN
.. . (let* ((fp (buffer-file-name)) (fn (file-name-nondirectory fp))) (save-match-data (if (string-match-t "[.][^.]*$" fn) (setq fn (replace-match "" nil t fn)))) (let ((args (concat " " fp " | ws_rst2man.py --traceback "))) (save-buffer) (compile (concat "PATH=\".:$PATH\"; cat " args))))

.. :ide: COMPILE: render reST as TXT (via MAN)
.. . (let* ((fp (buffer-file-name)) (fn (file-name-nondirectory fp))) (save-match-data (if (string-match-t "[.][^.]*$" fn) (setq fn (replace-match "" nil t fn)))) (let ((args (concat " " fp " | ws_rst2man.py --traceback | man -l -"))) (save-buffer) (compile (concat "PATH=\".:$PATH\"; cat " args))))

.. :ide: COMPILE: render reST as ODT --strip-comments
.. . (let* ((fp (buffer-file-name)) (fn (file-name-nondirectory fp))) (save-match-data (if (string-match-t "[.][^.]*$" fn) (setq fn (replace-match "" nil t fn)))) (let ((args (concat " " fp " | ws_rst2odt.py --traceback --strip-comments | cat >" fn ".odt "))) (save-buffer) (compile (concat "PATH=\".:$PATH\"; cat " args))))

.. :ide: COMPILE: render reST as LaTeX, compile PDF and view with gv
.. . (let* ((fp (buffer-file-name)) (fn (file-name-nondirectory fp))) (save-match-data (if (string-match-t "[.][^.]*$" fn) (setq fn (replace-match "" nil t fn)))) (let ((args (concat " " fp " | ws_rst2latex.py --traceback | tee " fn ".tex && pdflatex '\\nonstopmode\\input " fn ".tex' && gv " fn ".pdf"))) (save-buffer) (compile (concat "PATH=\".:$PATH\"; cat " args))))

.. :ide: COMPILE: render reST as PDF
.. . (let* ((fp (buffer-file-name)) (fn (file-name-nondirectory fp))) (save-match-data (if (string-match-t "[.][^.]*$" fn) (setq fn (replace-match "" nil t fn)))) (let ((args (concat " " fp " | ws_rst2pdf -e ws_docutils.raw_role >" fn ".pdf"))) (save-buffer) (compile (concat "PATH=\".:$PATH\"; cat " args))))

.. :ide: COMPILE: render reST as HTML
.. . (let* ((fp (buffer-file-name)) (fn (file-name-nondirectory fp))) (save-match-data (if (string-match-t "[.][^.]*$" fn) (setq fn (replace-match "" nil t fn)))) (let ((args (concat " " fp " | ws_rst2html.py --traceback --cloak-email-addresses | tee " fn ".html "))) (save-buffer) (compile (concat "PATH=\".:$PATH\"; cat " args))))

.. :ide: COMPILE: render reST as pseudoXML
.. . (let* ((fp (buffer-file-name)) (fn (file-name-nondirectory fp))) (save-match-data (if (string-match-t "[.][^.]*$" fn) (setq fn (replace-match "" nil t fn)))) (let ((args (concat " --traceback " fp " 2>&1 #| tee " fn ".pxml"))) (save-buffer) (compile (concat "PATH=\".:$PATH\"; ws_rst2pseudoxml.py " args))))

.. :ide: +#-
.. . Process ()

.. :ide: QUO: ~~ Subsubsection ~~
.. . (insert "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\:rem\:`|\:sec\:|`\\ ::fillme\::\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n" )

.. :ide: QUO: -- Subsection --
.. . (insert "--------------------------------------------------\n\:rem\:`||\:sec\:||`\\ ::fillme\::\n--------------------------------------------------\n" )

.. :ide: QUO: == Section ==
.. . (insert "==================================================\n\:rem\:`|||\:sec\:|||`\\ ::fillme\::\n==================================================\n" )

.. :ide: +#-
.. . Sections ()

.. :ide: MENU-OUTLINE:  `|||:section:|||' (default)
.. . (x-eIDE-menu-outline "sec" '("|:" ":|") (cons (cons "^" ".. ") (cons nil nil)) "\\(_`[^`\n]+`\\|\\[[^]\n]+\\]\\|[|][^|\n]+[|]\\|[^:\n]+::\\)")

.. 
.. Local Variables:
.. mode: rst
.. snip-mode: rst
.. truncate-lines: t
.. symbol-tag-symbol-regexp: "[-0-9A-Za-z_#]\\([-0-9A-Za-z_. ]*[-0-9A-Za-z_]\\|\\)"
.. symbol-tag-auto-comment-mode: nil
.. symbol-tag-srx-is-safe-with-nil-delimiters: nil
.. End:
