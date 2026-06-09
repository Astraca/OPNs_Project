import { request } from "./request";
import type { AuthResponse, AuthUser, LoginPayload, RegisterPayload } from "../types/auth";


export async function login(payload: LoginPayload) {
  const { data } = await request.post<AuthResponse>("/auth/login", payload);
  return data;
}

export async function register(payload: RegisterPayload) {
  const { data } = await request.post<AuthResponse>("/auth/register", payload);
  return data;
}

export async function getCurrentUser() {
  const { data } = await request.get<AuthUser>("/auth/me");
  return data;
}
