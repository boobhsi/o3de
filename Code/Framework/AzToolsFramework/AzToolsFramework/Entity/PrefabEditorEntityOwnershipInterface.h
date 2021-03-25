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

#pragma once

#include <AzCore/Component/Entity.h>
#include <AzCore/std/smart_ptr/unique_ptr.h>
#include <AzCore/std/string/string.h>

#include <AzToolsFramework/Prefab/Instance/Instance.h>

namespace AzToolsFramework
{
    class PrefabEditorEntityOwnershipInterface
    {
    public:
        AZ_RTTI(PrefabEditorEntityOwnershipInterface,"{38E764BA-A089-49F3-848F-46018822CE2E}");

        //! Creates a prefab instance with the provided entities and nestedPrefabInstances.
        //! /param entities The entities to put under the new prefab.
        //! /param nestedPrefabInstances The nested prefab instances to put under the new prefab.
        //! /param filePath The filepath corresponding to the prefab file to be created.
        //! /param instanceToParentUnder The instance under which the newly created prefab instance is parented under.
        //! /return The optional reference to the prefab created.
        virtual Prefab::InstanceOptionalReference CreatePrefab(
            const AZStd::vector<AZ::Entity*>& entities, AZStd::vector<AZStd::unique_ptr<Prefab::Instance>>&& nestedPrefabInstances,
            const AZStd::string& filePath, Prefab::Instance& instanceToParentUnder) = 0;
        virtual Prefab::InstanceOptionalReference GetRootPrefabInstance() = 0;
    };
}