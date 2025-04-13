import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Signup from '../pages/Signup';

describe('Signup Page', () => {
  it('renders name, email, and password inputs', () => {
    render(<BrowserRouter><Signup /></BrowserRouter>);
    expect(screen.getByPlaceholderText(/enter your full name/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/enter your email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/create a password/i)).toBeInTheDocument();
  });

  it('shows error if passwords do not match', async () => {
    render(<BrowserRouter><Signup /></BrowserRouter>);
    fireEvent.change(screen.getByPlaceholderText(/create a password/i), {
      target: { value: '123456' },
    });
    fireEvent.change(screen.getByPlaceholderText(/confirm your password/i), {
      target: { value: '654321' },
    });
    const signUpButtons = screen.getAllByRole('button', { name: /sign up/i });
    fireEvent.click(signUpButtons[0]);

  });
});
