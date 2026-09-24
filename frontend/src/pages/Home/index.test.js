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
        ok: true,
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
      essay_constraints: { min: 4.5, max: 15 },
      port_red_objective: 'none',
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

  test('envia limites decimais e objetivo separado de Redação', async () => {
    render(<HomePage />);

    await userEvent.clear(screen.getByLabelText('Nota mínima da Redação'));
    await userEvent.type(screen.getByLabelText('Nota mínima da Redação'), '7.3');
    await userEvent.selectOptions(screen.getByLabelText('Objetivo de Português e Redação'), 'essay');
    await userEvent.click(screen.getByRole('button', { name: /otimizar/i }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const payload = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(payload.essay_constraints).toEqual({ min: 7.3, max: 15 });
    expect(payload.port_red_objective).toBe('essay');
    expect(payload.min_subjects).not.toContain('PORT_RED');
  });
});
