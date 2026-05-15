export interface MenuCapability {
  key: string;
  label: string;
  description: string;
  required_scopes: string[];
  visible: boolean;
}

export interface UserInfo {
  user_id: string;
  username: string;
  display_name: string;
  role: string;
  role_label: string;
  permissions: string[];
}

export interface AuthProfile {
  user_id: string;
  username: string;
  display_name: string;
  role: string;
  role_label: string;
  permissions: string[];
  roles: string[];
  menus: MenuCapability[];
}

export interface LoginResponse {
  code: number;
  data: {
    access_token: string;
    token_type: string;
    user: UserInfo;
  };
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
  permissions: PermissionDefinition[];
  roles: RoleDefinition[];
  menus: MenuDefinition[];
}
