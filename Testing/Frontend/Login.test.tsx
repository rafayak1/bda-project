import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../pages/Login';

describe('Login Page', () => {
  it('renders email and password inputs', () => {
    render(<BrowserRouter><Login /></BrowserRouter>);
    expect(screen.getByPlaceholderText(/enter your email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/enter your password/i)).toBeInTheDocument();
  });

  it('validates empty form submission', () => {
    render(<BrowserRouter><Login /></BrowserRouter>);
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
  });
});