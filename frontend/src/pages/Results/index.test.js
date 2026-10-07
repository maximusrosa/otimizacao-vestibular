import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Results from './index';
import { __setLocationState as setLocationState } from 'react-router-dom';

const routeState = {
  results: {
    AC: 700,
    threshold: 680,
    chosen_hits: {},
  },
  historicalData: {},
  simulation: {
    course: 'Ciência da Computação - Bacharelado',
    referenceYear: '2025',
    entryMethod: 'LI_EP',
  },
};

const rankingResponse = {
  items: [{
    position: 11,
    source_classification: 14,
    name: 'Candidata Exemplo',
    final_score: 700,
    remapped_vacancy: null,
    competition_vacancies: 'LI_EP',
    entry_vacancy: 'LI_EP',
    status: 'Matriculado',
    status_date: '2025-02-10',
  }],
  total: 40,
  offset: 10,
  limit: 25,
  simulated_position: 12,
  anchor_index: 11,
  last_synced_at: '2025-02-11T08:00:00+00:00',
  is_stale: false,
};

describe('Results ranking', () => {
  beforeEach(() => {
    setLocationState(routeState);
    global.fetch = jest.fn((url) => {
      if (url.endsWith('/entry-modes')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(['AC', 'LI_EP']) });
      }
      if (url.includes('/rankings/candidates?')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(rankingResponse) });
      }
      return Promise.resolve({ ok: false, status: 404 });
    });
  });

  afterEach(() => {
    setLocationState({});
    jest.restoreAllMocks();
  });

  test('abre na modalidade otimizada e mostra candidato e simulação', async () => {
    render(<Results />);

    expect(await screen.findByText('Candidata Exemplo')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Modalidade' })).toHaveValue('LI_EP'));
    expect(screen.getByText('Sua simulação')).toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();

    const rankingCall = global.fetch.mock.calls.find(([url]) => url.includes('/rankings/candidates?'));
    expect(rankingCall[0]).toContain('entry_mode=LI_EP');
    expect(rankingCall[0]).toContain('anchor_score=700');
    expect(rankingCall[0]).not.toContain('offset=');
  });

  test('permite trocar para o curso inteiro e navegar pela janela', async () => {
    render(<Results />);
    await screen.findByText('Candidata Exemplo');

    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Modalidade' }), '');
    await waitFor(() => {
      const calls = global.fetch.mock.calls.filter(([url]) => url.includes('/rankings/candidates?'));
      expect(calls).toHaveLength(2);
    });
    let rankingCalls = global.fetch.mock.calls.filter(([url]) => url.includes('/rankings/candidates?'));
    expect(rankingCalls.at(-1)[0]).not.toContain('entry_mode=');

    await userEvent.click(await screen.findByRole('button', { name: 'Próxima' }));
    await waitFor(() => {
      const calls = global.fetch.mock.calls.filter(([url]) => url.includes('/rankings/candidates?'));
      expect(calls).toHaveLength(3);
    });
    rankingCalls = global.fetch.mock.calls.filter(([url]) => url.includes('/rankings/candidates?'));
    expect(rankingCalls.at(-1)[0]).toContain('offset=35');
  });
});
