# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LatLngJump
                                 A QGIS plugin
 LatLng Jump
                              -------------------
        begin                : 2017-09-13
        git sha              : $Format:%H$
        copyright            : (C) 2017 by tkykwtnb
        email                : tkykwtnb@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QMessageBox
# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from latlng_jump_dockwidget import LatLngJumpDockWidget
import os.path

from qgis.gui import QgsMapToolEmitPoint
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPoint
import re


class LatLngJump:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LatLngJump_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&LatLng Jump')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'LatLngJump')
        self.toolbar.setObjectName(u'LatLngJump')

        #print "** INITIALIZING LatLngJump"

        self.pluginIsActive = False
        self.dockwidget = None

        self.canvas = self.iface.mapCanvas()
        self.map_tool = QgsMapToolEmitPoint(self.canvas)


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('LatLngJump', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/LatLngJump/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'LatLng Jump'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.map_tool.canvasClicked.connect(self.getClickedLatLng)

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING LatLngJump"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD LatLngJump"

        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&LatLng Jump'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING LatLngJump"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = LatLngJumpDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            self.dockwidget.pushButton_Jump.clicked.connect(self.jumpToLatLng)
            self.dockwidget.pushButton_Capture.clicked.connect(self.enableCapture)

            self.dockwidget.lineEdit_Scale.setText("1:" + str(int(round(self.canvas.scale()))))
            self.dockwidget.comboBox_EPSG.addItem("4326")
            self.dockwidget.comboBox_EPSG.addItem("3857")
#            self.dockwidget.comboBox_EPSG.activated[str].connect(self.selectionchange)


    #--------------------------------------------------------------------------

    def jumpToLatLng(self):
        # Input check
        inputStatus = True

        inputCRSStr = self.dockwidget.comboBox_EPSG.currentText()
        if not re.match("^[1-9]\d*$", inputCRSStr):
            inputStatus = False

        if not self.dockwidget.checkBox_Scale.isChecked():
            targetScaleStr = self.dockwidget.lineEdit_Scale.text()
            if not (re.match("^([1-9]\d*|0)(\.\d+)?:([1-9]\d*|0)(\.\d+)?$", targetScaleStr) or
                re.match("^([1-9]\d*|0)(\.\d+)$", targetScaleStr)):
                inputStatus = False

        targetLatLngStr = self.dockwidget.lineEdit_Jump.text()
        if not re.match("^([-]?[1-9]\d*|0)(\.\d+)?([,|/|:|\s]+)([-]?[1-9]\d*|0)(\.\d+)?$", targetLatLngStr):
            inputStatus = False

        # Jump to targetPoint
        if inputStatus:
            targetLat, targetLng = re.split(r'[,|/|:|\s]+', targetLatLngStr)

            inputCRS = QgsCoordinateReferenceSystem(int(inputCRSStr))
            targetPoint = QgsPoint(float(targetLng), float(targetLat))
            canvasCRSStr = self.canvas.mapRenderer().destinationCrs().authid()
            canvasCRSStr = canvasCRSStr.replace("EPSG:", "")
            canvasCRS = QgsCoordinateReferenceSystem(int(canvasCRSStr))

            if inputCRS != canvasCRS:
                xform = QgsCoordinateTransform(inputCRS, canvasCRS)
                targetPoint = xform.transform(targetPoint)

            if not self.dockwidget.checkBox_Scale.isChecked():
                if ":" in targetScaleStr:
                    ts_left, ts_right = targetScaleStr.split(":")
                    targetScale = float(ts_right) / float(ts_left)
                else:
                    targetScale = float(targetScaleStr)
                self.canvas.zoomScale(targetScale)

            self.canvas.setCenter(targetPoint)
            self.canvas.refresh()
        else:
            QMessageBox.critical(self.iface.mainWindow(), "Error", "Format error.")


    def enableCapture(self):
        self.canvas.setMapTool(self.map_tool)


    def getClickedLatLng(self, point, button):
        if button == Qt.LeftButton:
            canvasCRS = self.canvas.mapRenderer().destinationCrs().authid()
            canvasCRS = canvasCRS.replace("EPSG:", "")

            targetCRS = self.dockwidget.comboBox_EPSG.currentText()

            srcCRS = QgsCoordinateReferenceSystem(int(canvasCRS))
            if canvasCRS == targetCRS:
                self.dockwidget.lineEdit_Capture.setText(str(point.y()) + ',' + str(point.x()))
            else:
                dstCRS = QgsCoordinateReferenceSystem(int(targetCRS))
                xform = QgsCoordinateTransform(srcCRS, dstCRS)
                point_2 = xform.transform(point)
                self.dockwidget.lineEdit_Capture.setText(str(point_2.y()) + ',' + str(point_2.x()))
        elif button == Qt.RightButton:
            self.canvas.unsetMapTool(self.map_tool)
            self.iface.actionPan().trigger()
