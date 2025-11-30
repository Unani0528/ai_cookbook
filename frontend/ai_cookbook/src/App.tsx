import { BrowserRouter, Routes, Route } from 'react-router-dom';
import RecipeGenerator from './components/RecipeGenerator';
import ChatPage from './components/ChatPage';
import RecipeResultPage from './components/RecipeResultPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RecipeGenerator />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/recipe-result" element={<RecipeResultPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
