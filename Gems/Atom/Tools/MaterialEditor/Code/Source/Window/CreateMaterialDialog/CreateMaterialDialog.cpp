/*
* All or portions of this file Copyright (c) Amazon.com, Inc. or its affiliates or
* its licensors.
*
* For complete copyright and license terms please see the LICENSE at the root of this
* distribution (the "License"). All use of this software is governed by the License,
* or, if provided, by the license below or the license accompanying this file. Do not
* remove or modify any license notices. This file is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*
*/

#include <Window/CreateMaterialDialog/CreateMaterialDialog.h>

#include <AzFramework/Application/Application.h>
#include <AzFramework/StringFunc/StringFunc.h>

#include <AtomToolsFramework/Util/Util.h>

#include <Atom/RPI.Edit/Common/AssetUtils.h>
#include <Atom/RPI.Edit/Material/MaterialSourceData.h>
#include <Atom/RPI.Edit/Material/MaterialTypeSourceData.h>

#include <QFileDialog>

namespace MaterialEditor
{
    CreateMaterialDialog::CreateMaterialDialog(QWidget* parent)
        : QDialog(parent)
        , m_ui(new Ui::CreateMaterialDialog)
    {
        m_ui->setupUi(this);

        InitMaterialTypeSelection();
        InitMaterialFileSelection();

        //Connect ok and cancel buttons
        QObject::connect(m_ui->m_buttonBox, &QDialogButtonBox::accepted, this, &QDialog::accept);
        QObject::connect(m_ui->m_buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
    }

    void CreateMaterialDialog::InitMaterialTypeSelection()
    {
        //Locate all material type files and add them to the combo box
        AZ::Data::AssetCatalogRequests::AssetEnumerationCB enumerateCB = [this]([[maybe_unused]] const AZ::Data::AssetId id, const AZ::Data::AssetInfo& info)
        {
            if (AzFramework::StringFunc::EndsWith(info.m_relativePath.c_str(), AZ::RPI::MaterialTypeSourceData::Extension))
            {
                const AZStd::string& sourcePath = AZ::RPI::AssetUtils::GetSourcePathByAssetId(info.m_assetId);
                if (!sourcePath.empty())
                {
                    m_materialTypeFileInfo = QFileInfo(sourcePath.c_str());
                    m_ui->m_materialTypeComboBox->addItem(m_materialTypeFileInfo.baseName(), QVariant(m_materialTypeFileInfo.absoluteFilePath()));
                }
            }
        };

        AZ::Data::AssetCatalogRequestBus::Broadcast(&AZ::Data::AssetCatalogRequestBus::Events::EnumerateAssets, nullptr, enumerateCB, nullptr);

        //Update the material type file info whenever the combo box selection changes 
        QObject::connect(m_ui->m_materialTypeComboBox, static_cast<void(QComboBox::*)(const int)>(&QComboBox::currentIndexChanged), m_ui->m_materialTypeComboBox, [this](int index) {
            QVariant data = m_ui->m_materialTypeComboBox->itemData(index);
            m_materialTypeFileInfo = QFileInfo(data.toString());
            });

        //Select StandardPBR by default but we will later data drive this with editor settings
        m_ui->m_materialTypeComboBox->setCurrentText("StandardPBR");
    }

    void CreateMaterialDialog::InitMaterialFileSelection()
    {
        //Select a default location and unique name for the new material
        m_materialFileInfo = AtomToolsFramework::GetUniqueFileInfo(
            QString(AZ::IO::FileIOBase::GetInstance()->GetAlias("@devassets@")) +
            AZ_CORRECT_FILESYSTEM_SEPARATOR + "Materials" +
            AZ_CORRECT_FILESYSTEM_SEPARATOR + "untitled." +
            AZ::RPI::MaterialSourceData::Extension).absoluteFilePath();

        m_ui->m_materialFilePicker->setLineEditReadOnly(true);
        m_ui->m_materialFilePicker->setText(m_materialFileInfo.fileName());

        //When the file selection button is pressed, open a file dialog to select where the material will be saved
        QObject::connect(m_ui->m_materialFilePicker, &AzQtComponents::BrowseEdit::attachedButtonTriggered, m_ui->m_materialFilePicker, [this]() {
            QFileInfo fileInfo = QFileDialog::getSaveFileName(this,
                QString("Select Material Filename"),
                m_materialFileInfo.absoluteFilePath(),
                QString("Material (*.material)"));

            //Reject empty or invalid filenames which indicate user cancellation
            if (!fileInfo.absoluteFilePath().isEmpty())
            {
                m_materialFileInfo = fileInfo;
                m_ui->m_materialFilePicker->setText(m_materialFileInfo.fileName());
            }
            });
    }

} // namespace MaterialEditor

#include <Window/CreateMaterialDialog/moc_CreateMaterialDialog.cpp>