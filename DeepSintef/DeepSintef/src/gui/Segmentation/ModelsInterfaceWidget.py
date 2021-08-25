from __main__ import qt, ctk, slicer, vtk
from glob import glob
import os
import json
from collections import OrderedDict
import subprocess
import sys
if sys.version_info.major == 3:
    from functools import reduce

from src.utils.resources import SharedResources
from src.logic.model_parameters import *
from src.DeepSintefLogic import DeepSintefLogic
from src.utils.io_utilities import get_available_cloud_models_list, download_cloud_model, download_cloud_model_thread


class ModelsInterfaceWidget(qt.QWidget):
    """
    GUI component displaying the local and remote available models, together with a description.
    Initialize the selected model's parameters.
    """
    def __init__(self, parent=None):
        super(ModelsInterfaceWidget, self).__init__(parent)
        self.base_layout = qt.QVBoxLayout()
        self.setup_cloud_models_area()
        self.setup_local_models_area()
        self.populate_local_models()
        self.populate_cloud_models()
        self.setup_model_parameters_area()
        self.setLayout(self.base_layout)
        self.setup_connections()
        self.on_model_selection(0)

    def setup_cloud_models_area(self):
        self.cloud_models_area_groupbox = ctk.ctkCollapsibleGroupBox()
        self.cloud_models_area_groupbox.setTitle("Available cloud Models")
        self.base_layout.addWidget(self.cloud_models_area_groupbox)
        # Layout within the dummy collapsible button
        self.cloudmodelsFormLayout = qt.QFormLayout(self.cloud_models_area_groupbox)

        # model search
        self.cloud_models_area_searchbox = ctk.ctkSearchBox()
        self.cloudmodelsFormLayout.addRow("Search:", self.cloud_models_area_searchbox)

        # model selector
        self.cloud_model_selector_combobox = qt.QComboBox()
        self.cloudmodelsFormLayout.addRow("Model:", self.cloud_model_selector_combobox)

        self.cloud_model_download_pushbutton = qt.QPushButton('Press to download')
        self.cloudmodelsFormLayout.addRow("Download:", self.cloud_model_download_pushbutton)
        self.cloud_model_download_pushbutton.setEnabled(False)

    def setup_local_models_area(self):
        self.local_models_area_groupbox = ctk.ctkCollapsibleGroupBox()
        self.local_models_area_groupbox.setTitle("Local Models")
        self.base_layout.addWidget(self.local_models_area_groupbox)
        # Layout within the dummy collapsible button
        self.modelsFormLayout = qt.QFormLayout(self.local_models_area_groupbox)

        # model search
        self.local_models_area_searchbox = ctk.ctkSearchBox()
        self.modelsFormLayout.addRow("Search:", self.local_models_area_searchbox)

        # model selector
        self.local_model_selector_combobox = qt.QComboBox()
        self.modelsFormLayout.addRow("Model:", self.local_model_selector_combobox)

        self.local_model_moreinfo_pushbutton = qt.QPushButton('Press to display')
        self.modelsFormLayout.addRow("Details:", self.local_model_moreinfo_pushbutton)
        self.local_model_moreinfo_pushbutton.setEnabled(False)

    def setup_model_parameters_area(self):
        # Parameters Area
        parametersCollapsibleButton = ctk.ctkCollapsibleGroupBox()
        parametersCollapsibleButton.setTitle("Model Parameters")
        self.base_layout.addWidget(parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        self.model_parameters = ModelParameters(parametersCollapsibleButton)

    def setup_connections(self):
        self.cloud_models_area_searchbox.connect("textChanged(QString)", self.on_cloud_model_search)
        self.cloud_model_selector_combobox.connect('currentIndexChanged(int)', self.on_cloud_model_selection)
        self.cloud_model_download_pushbutton.connect('clicked()', self.on_cloud_model_download_selected)
        # self.cloud_model_download_pushbutton.connect('clicked()', self.on_cloud_model_download_selected2)

        self.local_models_area_searchbox.connect("textChanged(QString)", self.on_local_model_search)
        self.local_model_selector_combobox.connect('currentIndexChanged(int)', self.on_model_selection)
        self.local_model_moreinfo_pushbutton.connect('clicked()', self.on_model_details_selected)

    def on_cloud_model_selection(self, index):
        pass

    def on_cloud_model_search(self, searchText):
        # add all the models listed in the json files
        self.cloud_model_selector_combobox.clear()
        # split text on whitespace of and string search
        searchTextList = searchText.split()
        for item in self.cloud_models_list:
            lname = item[0].lower()
            if 'segmentation' in lname:
                # require all elements in list, to add to select. case insensitive
                if reduce(lambda x, y: x and (lname.find(y.lower()) != -1), [True] + searchTextList):
                    self.cloud_model_selector_combobox.addItem(item[0])

    def on_cloud_model_download_selected2(self):
        popup = qt.QMessageBox()
        popup.setWindowTitle('Downloading\n')
        popup.setText('plop')
        x = popup.exec_()

    def on_cloud_model_download_selected(self):
        # mainWindow = slicer.util.mainWindow()
        # downloadWidget = qt.QWidget()
        # layout = qt.QVBoxLayout()
        # downloadWidget.setLayout(layout)
        # popupGeometry = qt.QRect()
        # if mainWindow:
        #     width = 400
        #     height = 200
        #     popupGeometry.setWidth(width)
        #     popupGeometry.setHeight(height)
        #     downloadWidget.setGeometry(popupGeometry)
        #
        # pos = mainWindow.pos
        # downloadWidget.move(pos.x() + (mainWindow.width - downloadWidget.width) / 2,
        #                     pos.y() + (mainWindow.height - downloadWidget.height) / 2)
        #
        # titleLabel = qt.QLabel('Download box')
        # layout.addWidget(titleLabel)
        # te = qt.QTextEdit('plop')
        # te.readOnly = True
        # layout.addWidget(te)
        # closeButton = qt.QPushButton('Close')
        # layout.addWidget(closeButton)
        # downloadWidget.show()

        # popup = qt.QMessageBox()
        # popup.setWindowTitle('Downloading\n')
        # popup.setText('plop')
        # x = popup.exec_()

        selected_model = self.cloud_model_selector_combobox.currentText
        # success = download_cloud_model_thread(selected_model, self.jsonModels, self.cloud_models_list)
        success = download_cloud_model(selected_model, self.jsonModels, self.cloud_models_list)
        if success:
            self.populate_local_models()
            self.populate_cloud_models()

    def populate_cloud_models(self):
        self.cloud_models_list = []
        self.cloud_model_selector_combobox.clear()
        cloud_models_list = get_available_cloud_models_list()
        for idx, model in enumerate(cloud_models_list):
            already_local = True if True in [x["name"] == model[0] for x in self.jsonModels] else False
            if not already_local:
                self.cloud_models_list.append(model)
                self.cloud_model_selector_combobox.addItem(model[0], idx)

        if len(self.cloud_models_list) >= 1:
            self.cloud_model_download_pushbutton.setEnabled(True)
        else:
            self.cloud_model_download_pushbutton.setEnabled(False)

    def on_model_selection(self, index):
        # print("on model select")
        self.model_parameters.destroy()
        if index < 0 or self.local_model_selector_combobox.count == 0:
            return
        jsonIndex = self.local_model_selector_combobox.itemData(index)
        json_model = self.jsonModels[jsonIndex]
        self.model_parameters.create(json_model)

        if "briefdescription" in self.jsonModels[jsonIndex]:
            tip = self.jsonModels[jsonIndex]["briefdescription"]
            tip = tip.rstrip()
            self.local_model_selector_combobox.setToolTip(tip)
        else:
            self.local_model_selector_combobox.setToolTip("")

        # self.enable_user_interface(True)
        #self.onLocateButton()
        DeepSintefLogic.getInstance().selected_model = self.local_model_selector_combobox

    def on_local_model_search(self, searchText):
        # add all the models listed in the json files
        self.local_model_selector_combobox.clear()
        # split text on whitespace of and string search
        searchTextList = searchText.split()
        for idx, j in enumerate(self.jsonModels):
            lname = j["name"].lower()
            if 'task' in j and j['task'] == 'Segmentation':
                # require all elements in list, to add to select. case insensitive
                if reduce(lambda x, y: x and (lname.find(y.lower()) != -1), [True] + searchTextList):
                    self.local_model_selector_combobox.addItem(j["name"], idx)

    def populate_local_models(self):
        digests = self.get_existing_digests()
        jsonFiles = glob(SharedResources.getInstance().json_local_dir + "/*.json")
        jsonFiles = sorted(jsonFiles)
        #jsonFiles.sort(cmp=lambda x, y: cmp(os.path.basename(x), os.path.basename(y)))
        self.jsonModels = []
        self.local_model_selector_combobox.clear()
        for fname in jsonFiles:
            with open(fname, "r") as fp:
                j = json.load(fp, object_pairs_hook=OrderedDict)

            self.jsonModels.append(j)
            # if j['docker']['digest'] in digests:
            #     self.jsonModels.append(j)
            # else:
            #     os.remove(fname)
        # add all the models listed in the json files
        # print('JSON models: {}'.format(self.jsonModels))
        for idx, j in enumerate(self.jsonModels):
            name = j["name"]
            if 'task' in j and j['task'] == 'Segmentation':
                self.local_model_selector_combobox.addItem(name, idx)

        if len(self.jsonModels) >= 1:
            self.local_model_moreinfo_pushbutton.setEnabled(True)
        else:
            self.local_model_moreinfo_pushbutton.setEnabled(False)

    def get_existing_digests(self):
        cmd = []
        cmd.append(SharedResources.getInstance().docker_path)
        cmd.append('images')
        cmd.append('--digests')
        # print(cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        digest_index = 2
        digests = []
        try:
            while True:
                slicer.app.processEvents()
                line = p.stdout.readline()
                if not line:
                    break
                line = line.split()
                if 'DIGEST' in line:
                    digest_index = line.index('DIGEST')
                else:
                    digests.append(line[digest_index])
        except Exception as e:
            print("Exception: {}".format(e))
        return digests

    def on_model_details_selected(self):
        index = self.local_model_selector_combobox.currentIndex
        #model_json = self.jsonModels[index]
        model_json = self.jsonModels[[x['name'] == self.local_model_selector_combobox.currentText for x in self.jsonModels].index(True)]

        tip = ''
        exhaustive_list = ['owner', 'task', 'organ', 'target', 'modality', 'sequence', 'dataset_description',
                           'briefdescription', 'detaileddescription']
        for a in exhaustive_list:
            if a in model_json:
                tip = tip + '\n' + a + ':' + model_json[a]

        #self.local_model_selector_combobox.setToolTip(tip)
        popup = qt.QMessageBox()
        popup.setWindowTitle('Exhaustive description for {}'.format(self.local_model_selector_combobox.currentText))
        popup.setText(tip)
        x = popup.exec_()
