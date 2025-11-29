import { useState, useCallback, useEffect } from "react";
import {
  recipeApi,
  InitSessionRequest,
  ChatHistoryItem,
  FinalRecipeResponse,
  SessionInfo,
} from "./recipeApi";

// ============ 1페이지: useInitSession 훅 ============

interface UseInitSessionReturn {
  isLoading: boolean;
  error: string | null;
  initSession: (data: InitSessionRequest) => Promise<{
    sessionId: string;
    initialMessage: string;
  } | null>;
}

export function useInitSession(): UseInitSessionReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initSession = useCallback(async (data: InitSessionRequest) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await recipeApi.initSession(data);

      return {
        sessionId: response.session_id,
        initialMessage: response.initial_message,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "세션 초기화 실패";
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { isLoading, error, initSession };
}

// ============ 2페이지: useRecipeChat 훅 ============

interface UseRecipeChatReturn {
  messages: ChatHistoryItem[];
  isLoading: boolean;
  error: string | null;
  sessionInfo: SessionInfo | null;
  sendMessage: (message: string) => Promise<void>;
  finalizeRecipe: () => Promise<FinalRecipeResponse | null>;
  loadHistory: () => Promise<void>;
  clearError: () => void;
}

export function useRecipeChat(sessionId: string | null): UseRecipeChatReturn {
  const [messages, setMessages] = useState<ChatHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);

  // 세션 정보 및 히스토리 로드
  const loadHistory = useCallback(async () => {
    if (!sessionId) return;

    try {
      setIsLoading(true);

      // 세션 정보 로드
      const info = await recipeApi.getSessionInfo(sessionId);
      setSessionInfo(info);

      // 채팅 히스토리 로드
      const historyResponse = await recipeApi.getChatHistory(sessionId);
      setMessages(historyResponse.history);
    } catch (err) {
      const message = err instanceof Error ? err.message : "히스토리 로드 실패";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // 초기 로드
  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // 메시지 전송
  const sendMessage = useCallback(
    async (message: string) => {
      if (!sessionId) {
        setError("세션이 없습니다.");
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // 낙관적 업데이트
        setMessages((prev) => [...prev, { role: "user", content: message }]);

        const response = await recipeApi.sendMessage(sessionId, message);

        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: response.response },
        ]);
      } catch (err) {
        setMessages((prev) => prev.slice(0, -1));
        const errMessage = err instanceof Error ? err.message : "메시지 전송 실패";
        setError(errMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
  );

  // 레시피 확정
  const finalizeRecipe = useCallback(async (): Promise<FinalRecipeResponse | null> => {
    if (!sessionId) {
      setError("세션이 없습니다.");
      return null;
    }

    try {
      setIsLoading(true);
      setError(null);

      const result = await recipeApi.finalizeRecipe(sessionId);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : "레시피 확정 실패";
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const clearError = useCallback(() => setError(null), []);

  return {
    messages,
    isLoading,
    error,
    sessionInfo,
    sendMessage,
    finalizeRecipe,
    loadHistory,
    clearError,
  };
}

// ============ 3페이지: useFinalRecipe 훅 ============

interface UseFinalRecipeReturn {
  recipe: FinalRecipeResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useFinalRecipe(sessionId: string | null): UseFinalRecipeReturn {
  const [recipe, setRecipe] = useState<FinalRecipeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecipe = useCallback(async () => {
    if (!sessionId) return;

    try {
      setIsLoading(true);
      setError(null);

      const data = await recipeApi.getFinalRecipe(sessionId);
      setRecipe(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "레시피 조회 실패";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchRecipe();
  }, [fetchRecipe]);

  return {
    recipe,
    isLoading,
    error,
    refetch: fetchRecipe,
  };
}