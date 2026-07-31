import { render, screen } from '@testing-library/react';
import App from './App';

test('renderiza a página inicial (Otimizador)', () => {
  render(<App />);
  expect(
    screen.getByRole('heading', { name: /otimizador de acertos/i })
  ).toBeInTheDocument();
});
