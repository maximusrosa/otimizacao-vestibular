// Stub de react-router-dom para o jest (CRA 5 não segue o campo "exports" do
// react-router v7). Fornece apenas o que o app usa nos testes.
const navigate = jest.fn();

// Componentes de roteamento: renderizam os filhos sem lógica de rota real.
const BrowserRouter = ({ children }) => children;
const MemoryRouter = ({ children }) => children;
// Renderiza apenas a primeira rota (a "/" index), como uma SPA na home.
const Routes = ({ children }) => {
  const first = Array.isArray(children) ? children[0] : children;
  return first || null;
};
const Route = ({ element }) => element || null;

module.exports = {
  useNavigate: () => navigate,
  useLocation: () => ({ state: {} }),
  BrowserRouter,
  MemoryRouter,
  Routes,
  Route,
  __navigate: navigate, // acesso ao mock nos testes
};
