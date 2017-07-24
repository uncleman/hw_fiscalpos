DOCKER_IMAGE_NAME=$1

docker cp . $DOCKER_IMAGE_NAME:/usr/lib/python2.7/dist-packages/odoo/addons/point_of_sale/static/src/js

