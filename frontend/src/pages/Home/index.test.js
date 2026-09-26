import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HomePage from './index';
// react-router-dom é mapeado para um stub local (ver package.json > jest),
// porque o resolver do jest (CRA 5) não segue o campo "exports" do v7.
import { __navigate as mockNavigate } from 'react-router-dom';

describe('HomePage /optimize payload (dados mockados)', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    global.fetch = jest.fn((url) => {
      const responseByUrl = {
        'http://localhost:8000/years': ['2022', '2023', '2024', '2025'],
        'http://localhost:8000/foreign-languages': ['Inglês', 'Espanhol'],
        'http://localhost:8000/entry-modes': ['AC', 'LI_EP'],
        'http://localhost:8000/courses?reference_year=2025': ['Ciência da Computação - Bacharelado'],
        'http://localhost:8000/optimize': { result: {}, graphJson: {} },
      };

      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(responseByUrl[url]),
      });
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const fillRequiredFields = async () => {
    const [yearSelect, courseSelect, languageSelect, entryMethodSelect] =
      screen.getAllByRole('combobox');

    await waitFor(() => expect(yearSelect).toBeEnabled());
    await userEvent.selectOptions(yearSelect, '2025');
    await waitFor(() => expect(courseSelect).toBeEnabled());
    await userEvent.selectOptions(courseSelect, 'Ciência da Computação - Bacharelado');
    await userEvent.selectOptions(languageSelect, 'Inglês');
    await userEvent.selectOptions(entryMethodSelect, 'LI_EP');
  };

  test('envia foreign_language e demais campos exigidos pelo backend', async () => {
    render(<HomePage />);
    await fillRequiredFields();

    await userEvent.click(screen.getByRole('button', { name: /otimizar/i }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(5));

    const [url, options] = global.fetch.mock.calls.find(
      ([requestUrl]) => requestUrl === 'http://localhost:8000/optimize'
    );
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
    expect(payload).not.toHaveProperty('std_scores');
    expect(payload.constraints).toBeDefined();
    expect(Array.isArray(payload.min_subjects)).toBe(true);
  });

  test('navega para /resultados após resposta bem-sucedida', async () => {
    render(<HomePage />);
    await fillRequiredFields();

    await userEvent.click(screen.getByRole('button', { name: /otimizar/i }));

    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith(
        '/resultados',
        expect.objectContaining({ state: expect.any(Object) })
      )
    );
  });
});
