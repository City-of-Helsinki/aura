Installation
============

Database
--------

Shell commands:

    sudo su postgres
    createuser -R -S -D -P aura
    createdb -O aura -T template0 -l fi_FI.UTF8 -E utf8 aura
