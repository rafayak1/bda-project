import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Chaty from '../pages/Chaty';

describe('Chaty Component', () => {
  it('renders chat interface with placeholder', () => {
    render(<BrowserRouter><Chaty /></BrowserRouter>);
    expect(screen.getByPlaceholderText(/type your message here/i)).toBeInTheDocument();
    expect(screen.getByText(/upload dataset/i)).toBeInTheDocument();
  });
});
