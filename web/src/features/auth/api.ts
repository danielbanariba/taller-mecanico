import { http } from "../../shared/api/http";

export interface User {
  id: string;
  full_name: string;
  phone: string;
  role: string;
}

export interface Workshop {
  id: string;
  name: string;
}

/** Shape returned by every identity endpoint: `register`, `login`, `me`. */
export interface Me {
  user: User;
  workshop: Workshop;
}

export interface RegisterPayload {
  workshop_name: string;
  owner_name: string;
  phone: string;
  password: string;
}

export interface LoginPayload {
  phone: string;
  password: string;
}

export const authApi = {
  register: (payload: RegisterPayload) => http.post<Me>("/api/auth/register", payload),
  login: (payload: LoginPayload) => http.post<Me>("/api/auth/login", payload),
  logout: () => http.post<void>("/api/auth/logout"),
  me: () => http.get<Me>("/api/auth/me"),
};
