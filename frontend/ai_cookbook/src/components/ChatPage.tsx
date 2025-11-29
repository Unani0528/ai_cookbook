import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Send, ChefHat, User, Loader2 } from 'lucide-react';
import Header from './Header';
import Footer from './Footer';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const ChatPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // 세션 ID 가져오기 (1페이지에서 전달받음)
  useEffect(() => {
    const state = location.state as { sessionId?: string; initialMessage?: string };

    if (!state?.sessionId) {
      alert('세션 정보가 없습니다. 처음부터 다시 시작해주세요.');
      navigate('/');
      return;
    }

    setSessionId(state.sessionId);

    // 초기 메시지가 있으면 추가
    if (state.initialMessage) {
      setMessages([
        {
          role: 'assistant',
          content: state.initialMessage,
        },
      ]);
    }
  }, [location, navigate]);

  // 메시지 전송
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');

    // 사용자 메시지 즉시 추가
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/recipeChat/chat/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
        throw new Error('메시지 전송 실패');
      }

      const data = await response.json();

      // AI 응답 추가
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response },
      ]);
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      alert('메시지 전송 중 오류가 발생했습니다.');
      // 사용자 메시지 제거
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  // Enter 키로 전송
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 스크롤을 맨 아래로
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 레시피 확정 버튼
  const handleFinalizeRecipe = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`http://localhost:8000/recipeChat/finalize/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_confirmation: '레시피를 확정합니다.' }),
      });

      if (!response.ok) {
        throw new Error('레시피 확정 실패');
      }

      const data = await response.json();

      // 3페이지로 이동 (최종 레시피 페이지)
      navigate('/recipe-result', {
        state: {
          sessionId,
          recipe: data,
        },
      });
    } catch (error) {
      console.error('레시피 확정 오류:', error);
      alert('레시피 확정 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex flex-col">
      <Header />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col">
        {/* 페이지 제목 */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-6 py-3 rounded-full mb-4">
            <ChefHat className="w-5 h-5" />
            <span className="font-semibold">AI 레시피 챗봇</span>
          </div>
          <p className="text-gray-600">
            원하는 레시피에 대해 자유롭게 질문하고 수정해보세요
          </p>
        </div>

        {/* 채팅 메시지 영역 */}
        <div className="flex-1 bg-white rounded-2xl shadow-xl border border-gray-200 p-6 mb-4 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`flex gap-3 max-w-[80%] ${
                    msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  {/* 아바타 */}
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      <User className="w-5 h-5" />
                    ) : (
                      <ChefHat className="w-5 h-5" />
                    )}
                  </div>

                  {/* 메시지 내용 */}
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                  </div>
                </div>
              </div>
            ))}

            {/* 로딩 인디케이터 */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex gap-3 max-w-[80%]">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-gradient-to-r from-cyan-500 to-blue-500 text-white">
                    <ChefHat className="w-5 h-5" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl px-4 py-3">
                    <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 입력 영역 */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition disabled:bg-gray-100"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:from-gray-300 disabled:to-gray-400 text-white p-3 rounded-xl transition disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          {/* 레시피 확정 버튼 */}
          <div className="mt-3 pt-3 border-t border-gray-200">
            <button
              onClick={handleFinalizeRecipe}
              disabled={messages.length === 0}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-gray-300 disabled:to-gray-400 text-white font-semibold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition disabled:cursor-not-allowed"
            >
              이 레시피로 확정하기
            </button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default ChatPage;
