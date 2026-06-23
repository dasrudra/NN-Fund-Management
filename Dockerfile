FROM odoo:19.0

USER root

COPY ./addons /mnt/extra-addons
COPY ./docker/odoo.conf /etc/odoo/odoo.conf

RUN chown -R odoo:odoo /mnt/extra-addons /etc/odoo/odoo.conf

USER odoo
