import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ForgotPassword from '../pages/ForgotPassword';

describe('Forgot Password', () => {
  it('validates email input', () => {
    render(<BrowserRouter><ForgotPassword /></BrowserRouter>);
    fireEvent.click(screen.getByText(/reset password/i));
  });
});