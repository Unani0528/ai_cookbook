// ============ 타입 정의 ============

// 1페이지: 세션 초기화
export interface InitSessionRequest {
  allergy: string;
  preferences: string;
  cooking_level: "beginner" | "intermediate" | "advanced";
  food_type: string;
}

export interface InitSessionResponse {
  session_id: string;
  initial_message: string;
  message: string;
}

// 2페이지: 채팅
export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  is_recipe: boolean;
}

export interface ChatHistoryItem {
  role: "user" | "assistant";
  content: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  history: ChatHistoryItem[];
}

export interface SessionInfo {
  allergy: string[];
  preferences: string;
  cooking_level: string;
  food_type: string;
  is_finalized: boolean;
}

// 3페이지: 최종 레시피
export interface FinalRecipeRequest {
  user_confirmation?: string;
}

export interface FinalRecipeResponse {
  session_id: string;
  recipe_name: string;
  recipe_content: string;
  image_prompt: string;
  is_finalized: boolean;
}

// ============ API 클라이언트 ============

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class RecipeApiClient {
  private baseUrl: string;
  private basePath: string = "/recipeChat";

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${this.basePath}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API 요청 실패: ${response.status}`);
    }

    return response.json();
  }

  // ============ 1페이지: 세션 초기화 ============

  async initSession(data: InitSessionRequest): Promise<InitSessionResponse> {
    return this.request<InitSessionResponse>("/init", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // ============ 2페이지: 채팅 ============

  async sendMessage(sessionId: string, message: string): Promise<ChatResponse> {
    return this.request<ChatResponse>(`/chat/${sessionId}`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  }

  async getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
    return this.request<ChatHistoryResponse>(`/chat/${sessionId}/history`);
  }

  async getSessionInfo(sessionId: string): Promise<SessionInfo> {
    return this.request<SessionInfo>(`/session/${sessionId}/info`);
  }

  // ============ 2→3페이지: 레시피 확정 ============

  async finalizeRecipe(
    sessionId: string,
    confirmation?: string
  ): Promise<FinalRecipeResponse> {
    return this.request<FinalRecipeResponse>(`/finalize/${sessionId}`, {
      method: "POST",
      body: JSON.stringify({ user_confirmation: confirmation || "" }),
    });
  }

  // ============ 3페이지: 최종 레시피 조회 ============

  async getFinalRecipe(sessionId: string): Promise<FinalRecipeResponse> {
    return this.request<FinalRecipeResponse>(`/recipe/${sessionId}`);
  }

  // ============ 공통 ============

  async deleteSession(sessionId: string): Promise<{ message: string }> {
    return this.request(`/session/${sessionId}`, {
      method: "DELETE",
    });
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/health");
  }
}

export const recipeApi = new RecipeApiClient();
export default RecipeApiClient;