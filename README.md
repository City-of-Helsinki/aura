Architecture
============

![Architecture diagram](https://rawgithub.com/City-of-Helsinki/aura/master/Docs/architecture.svg)

Old architecture diagram
------------------------
![Old architecture diagram](https://rawgithub.com/City-of-Helsinki/aura/master/Docs/architecture-old.svg)

Installation
============

Database
--------

Shell commands:

    sudo su postgres
    createuser -R -S -D -P aura
    createdb -O aura -T template0 -l fi_FI.UTF8 -E utf8 aura
