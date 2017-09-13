# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LatLngJump
                                 A QGIS plugin
 LatLng Jump
                             -------------------
        begin                : 2017-09-13
        copyright            : (C) 2017 by tkykwtnb
        email                : tkykwtnb@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LatLngJump class from file LatLngJump.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .latlng_jump import LatLngJump
    return LatLngJump(iface)
