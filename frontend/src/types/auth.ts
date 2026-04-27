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
  inferred_roles: string[];
  token_roles: string[];
  roles: string[];
  role_source: string;
  role_claim_keys: string[];
  configured_role_claim_names: string[];
  role_claim_required: boolean;
  role_claim_alignment_status: string;
  audience: string[];
  token_claim_keys: string[];
  claim_preview: Record<string, unknown>;
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
  role_resolution: {
    preferred_source: string;
    fallback_source: string;
    token_role_claim_candidates: string[];
    description: string;
  };
  logto_claim_setup: {
    configured_claim_names: string[];
    role_claim_required: boolean;
    custom_jwt_function_name: string;
    custom_jwt_function_signature: string;
    recommended_script: string;
  };
}
