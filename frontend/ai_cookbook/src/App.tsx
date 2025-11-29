import { BrowserRouter, Routes, Route } from 'react-router-dom';
import RecipeGenerator from './components/RecipeGenerator';
import ChatPage from './components/ChatPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RecipeGenerator />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
