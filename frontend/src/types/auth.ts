export type AuthUser = {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export type LoginPayload = {
  username_or_email: string;
  password: string;
};

export type RegisterPayload = {
  username: string;
  email: string;
  password: string;
};
