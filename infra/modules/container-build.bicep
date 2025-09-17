param location string
param containerRegistryName string
param repositoryName string = 'voice-live-agent/app-voiceagent'
param imageTag string = 'latest'
param sourceLocation string
param identityId string
param tags object = {}

// Get reference to existing container registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2022-02-01-preview' existing = {
  name: containerRegistryName
}

// Get reference to the user assigned identity
resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: last(split(identityId, '/'))
}

// Grant the identity ACR Build permission
resource acrBuildRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: containerRegistry
  name: guid(subscription().id, resourceGroup().id, userAssignedIdentity.id, 'acrBuildRole')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8311e382-0749-4cb8-b61a-304f252e45ec') // AcrBuild role
    principalType: 'ServicePrincipal'
    principalId: userAssignedIdentity.properties.principalId
  }
}

// Use deployment script to build and push the container image
resource containerBuild 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'build-container-image'
  location: location
  tags: tags
  kind: 'AzureCLI'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    azCliVersion: '2.63.0'
    timeout: 'PT30M'
    retentionInterval: 'PT1H'
    environmentVariables: [
      {
        name: 'REGISTRY_NAME'
        value: containerRegistryName
      }
      {
        name: 'REPOSITORY_NAME'
        value: repositoryName
      }
      {
        name: 'IMAGE_TAG'
        value: imageTag
      }
      {
        name: 'SOURCE_LOCATION'
        value: sourceLocation
      }
    ]
    scriptContent: '''
      echo "Starting container build process..."
      
      # Login to Azure Container Registry
      az acr login --name $REGISTRY_NAME
      
      # Build and push the container image
      az acr build --registry $REGISTRY_NAME \
                   --image $REPOSITORY_NAME:$IMAGE_TAG \
                   --file server/Dockerfile \
                   $SOURCE_LOCATION
      
      echo "Container image built and pushed successfully"
      echo "Image: $REGISTRY_NAME.azurecr.io/$REPOSITORY_NAME:$IMAGE_TAG"
    '''
  }
  dependsOn: [acrBuildRole]
}

output imageName string = '${containerRegistryName}.azurecr.io/${repositoryName}:${imageTag}'
output buildId string = containerBuild.id
