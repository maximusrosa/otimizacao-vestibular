import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HomePage from './index';
// react-router-dom é mapeado para um stub local (ver package.json > jest),
// porque o resolver do jest (CRA 5) não segue o campo "exports" do v7.
import { __navigate as mockNavigate } from 'react-router-dom';

describe('HomePage /optimize payload (dados mockados)', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ result: {}, graphJson: {} }),
      })
    );
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('envia foreign_language e demais campos exigidos pelo backend', async () => {
    render(<HomePage />);

    await userEvent.click(screen.getByRole('button', { name: /otimizar/i }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/optimize');
    expect(options.method).toBe('POST');

    const payload = JSON.parse(options.body);

    // Campos obrigatórios do modelo UserData (backend/src/main.py)
    expect(payload).toMatchObject({
      course: 'Ciência da Computação - Bacharelado',
      foreign_language: 'Inglês', // regressão: ausência causava 422
      reference_year: '2025',
      entry_method: 'LI_EP',
    });
    expect(payload.constraints).toBeDefined();
    expect(Array.isArray(payload.min_subjects)).toBe(true);
  });

  test('navega para /resultados após resposta bem-sucedida', async () => {
    render(<HomePage />);

    await userEvent.click(screen.getByRole('button', { name: /otimizar/i }));

    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith(
        '/resultados',
        expect.objectContaining({ state: expect.any(Object) })
      )
    );
  });
});
