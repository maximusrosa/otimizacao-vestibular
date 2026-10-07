import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HomePage from './index';
import { __navigate as mockNavigate } from 'react-router-dom';

describe('HomePage /optimize payload', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    global.fetch = jest.fn((url) => {
      const responseByUrl = {
        'http://localhost:8000/years': ['2025', '2024'],
        'http://localhost:8000/foreign-languages': ['Inglês', 'Espanhol'],
        'http://localhost:8000/entry-modes': ['AC', 'LI_EP'],
        'http://localhost:8000/courses?reference_year=2025': ['Ciência da Computação - Bacharelado'],
        'http://localhost:8000/optimize': { result: {}, graphJson: {} },
      };
      return Promise.resolve({ ok: true, json: () => Promise.resolve(responseByUrl[url]) });
    });
  });

  afterEach(() => jest.restoreAllMocks());

  const fillRequiredFields = async () => {
    const yearSelect = screen.getByRole('combobox', { name: 'Ano' });
    await waitFor(() => expect(yearSelect).toBeEnabled());
    await userEvent.selectOptions(yearSelect, '2025');

    const courseSelect = screen.getByRole('combobox', { name: 'Selecione seu curso' });
    await waitFor(() => expect(courseSelect).toBeEnabled());
    await userEvent.selectOptions(courseSelect, 'Ciência da Computação - Bacharelado');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Língua Estrangeira' }), 'Inglês');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Forma de Acesso' }), 'LI_EP');
  };

  const optimizePayload = () => {
    const call = global.fetch.mock.calls.find(([url]) => url === 'http://localhost:8000/optimize');
    return JSON.parse(call[1].body);
  };

  test('envia todos os campos exigidos pelo backend', async () => {
    render(<HomePage />);
    await fillRequiredFields();
    await userEvent.click(screen.getByRole('button', { name: /otimizar/i }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(5));
    expect(optimizePayload()).toMatchObject({
      course: 'Ciência da Computação - Bacharelado',
      foreign_language: 'Inglês',
      reference_year: '2025',
      entry_method: 'LI_EP',
      essay_constraints: { min: 4.5, max: 15 },
      port_red_objective: 'none',
    });
  });

  test('navega para resultados após resposta bem-sucedida', async () => {
    render(<HomePage />);
    await fillRequiredFields();
    await userEvent.click(screen.getByRole('button', { name: /otimizar/i }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith(
      '/resultados',
      expect.objectContaining({ state: expect.any(Object) })
    ));
  });

  test('marca Português e Redação como objetivo conjunto', async () => {
    render(<HomePage />);
    await fillRequiredFields();

    await userEvent.clear(screen.getByLabelText('Nota mínima da Redação'));
    await userEvent.type(screen.getByLabelText('Nota mínima da Redação'), '7.3');
    await userEvent.click(screen.getByLabelText('Português'));
    await userEvent.click(screen.getByLabelText('Redação'));
    await userEvent.click(screen.getByRole('button', { name: /otimizar/i }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(5));
    const payload = optimizePayload();
    expect(payload.essay_constraints).toEqual({ min: 7.3, max: 15 });
    expect(payload.port_red_objective).toBe('combined');
    expect(payload.min_subjects).not.toContain('PORT_RED');
  });
});
