# Shared MIME Info

The shared-mime-info package contains:

- The core database of common MIME types, their file extensions and icon names.
- The update-mime-database command, used to extend the DB and install a new MIME data.
- The freedesktop.org shared MIME database spec.

It is used by GLib, GNOME, KDE, XFCE and many others.

For more information about the database see the [Shared MIME Info Specification here](https://www.freedesktop.org/wiki/Specifications/shared-mime-info-spec/).

## Installation

To install do:
```sh
$ meson _build -Dprefix=/usr
$ ninja -v -C _build install
```

It requires the glib development package to be installed as well as
gettext.
This database is translated at Transifex.


Please report bugs here:
  https://gitlab.freedesktop.org/xdg/shared-mime-info/issues

Getting involved in freedesktop.org projects guide:
  https://www.freedesktop.org/wiki/GettingInvolved/


## Useful reference links

IANA:
  https://www.iana.org/assignments/media-types/

KDE's old mime-types:
  http://websvn.kde.org/branches/KDE/3.5/kdelibs/mimetypes/

UNIX file tool and libmagic
  https://github.com/file/file
