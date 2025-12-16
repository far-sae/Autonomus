from azure.identity import ClientSecretCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from msgraph import GraphServiceClient
from typing import Any, Dict, List, Optional
import asyncio


class AzureClient:
    """Azure client wrapper for compliance scanning."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Azure client.
        
        Args:
            credentials: Dict with 'tenant_id', 'client_id', 'client_secret', 'subscription_id'
        """
        self.tenant_id = credentials['tenant_id']
        self.client_id = credentials['client_id']
        self.client_secret = credentials['client_secret']
        self.subscription_id = credentials.get('subscription_id')
        
        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
    
    def get_subscription_client(self):
        """Get subscription client."""
        return SubscriptionClient(self.credential)
    
    def get_resource_client(self):
        """Get resource management client."""
        return ResourceManagementClient(self.credential, self.subscription_id)
    
    def get_storage_client(self):
        """Get storage management client."""
        return StorageManagementClient(self.credential, self.subscription_id)
    
    def get_graph_client(self):
        """Get Microsoft Graph client."""
        return GraphServiceClient(self.credential)
    
    # Subscription Methods
    def list_subscriptions(self):
        """List all subscriptions."""
        client = self.get_subscription_client()
        subscriptions = []
        for sub in client.subscriptions.list():
            subscriptions.append({
                'id': sub.subscription_id,
                'display_name': sub.display_name,
                'state': sub.state
            })
        return subscriptions
    
    # Storage Methods
    def list_storage_accounts(self):
        """List all storage accounts."""
        client = self.get_storage_client()
        accounts = []
        for account in client.storage_accounts.list():
            accounts.append({
                'name': account.name,
                'id': account.id,
                'location': account.location,
                'kind': account.kind,
                'sku': account.sku.name if account.sku else None
            })
        return accounts
    
    def get_storage_account_properties(self, resource_group: str, account_name: str):
        """Get storage account properties."""
        client = self.get_storage_client()
        try:
            account = client.storage_accounts.get_properties(
                resource_group_name=resource_group,
                account_name=account_name
            )
            return {
                'encryption': account.encryption,
                'https_only': account.enable_https_traffic_only,
                'public_network_access': account.public_network_access,
                'minimum_tls_version': account.minimum_tls_version
            }
        except Exception:
            return None
    
    # Microsoft 365 / Entra ID Methods
    async def list_users(self):
        """List all Entra ID users."""
        graph_client = self.get_graph_client()
        users = []
        try:
            result = await graph_client.users.get()
            if result and result.value:
                for user in result.value:
                    users.append({
                        'id': user.id,
                        'user_principal_name': user.user_principal_name,
                        'display_name': user.display_name,
                        'account_enabled': user.account_enabled
                    })
        except Exception:
            pass
        return users
    
    async def get_user_mfa_status(self, user_id: str):
        """Get user MFA status."""
        graph_client = self.get_graph_client()
        try:
            # Get authentication methods
            methods = await graph_client.users.by_user_id(user_id).authentication.methods.get()
            mfa_enabled = len(methods.value) > 1 if methods and methods.value else False
            return {'mfa_enabled': mfa_enabled, 'methods': len(methods.value) if methods and methods.value else 0}
        except Exception:
            return {'mfa_enabled': False, 'methods': 0}
    
    async def list_conditional_access_policies(self):
        """List conditional access policies."""
        graph_client = self.get_graph_client()
        policies = []
        try:
            result = await graph_client.identity.conditional_access.policies.get()
            if result and result.value:
                for policy in result.value:
                    policies.append({
                        'id': policy.id,
                        'display_name': policy.display_name,
                        'state': policy.state
                    })
        except Exception:
            pass
        return policies
    
    def list_resource_groups(self):
        """List all resource groups."""
        client = self.get_resource_client()
        groups = []
        for group in client.resource_groups.list():
            groups.append({
                'name': group.name,
                'location': group.location,
                'id': group.id
            })
        return groups
