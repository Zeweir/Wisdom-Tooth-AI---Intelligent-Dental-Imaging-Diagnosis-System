export interface MenuCapability {
  key: string;
  label: string;
  description: string;
  required_scopes: string[];
  visible: boolean;
}

export interface AuthProfile {
  sub: string;
  client_id: string | null;
  organization_id: string | null;
  permissions: string[];
  roles: string[];
  audience: string[];
  menus: MenuCapability[];
}

export interface PermissionDefinition {
  key: string;
  label: string;
  description: string;
}

export interface RoleDefinition {
  key: string;
  label: string;
  description: string;
  scopes: string[];
}

export interface MenuDefinition {
  key: string;
  label: string;
  description: string;
  required_scopes: string[];
}

export interface RbacModel {
  resource: string;
  permissions: PermissionDefinition[];
  roles: RoleDefinition[];
  menus: MenuDefinition[];
}
