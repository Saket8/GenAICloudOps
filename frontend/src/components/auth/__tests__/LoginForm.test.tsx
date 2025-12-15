/**
 * Unit tests for LoginForm component
 * Tests user interactions, validation, and API integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from '../LoginForm';
import { AuthProvider } from '../../../contexts/AuthContext';
import { configureServer } from '../../../mocks/server';
import { createTestQueryClient, createMockUser, checkAccessibility } from '../../../test-setup';

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = createTestQueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {children}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const renderLoginForm = (props = {}) => {
  return render(
    <TestWrapper>
      <LoginForm {...props} />
    </TestWrapper>
  );
};

describe('LoginForm - Unit Tests', () => {
  beforeEach(() => {
    configureServer.success();
  });

  describe('Rendering', () => {
    test('should render login form with all required elements', () => {
      renderLoginForm();

      expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
      expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
    });

    test('should have proper form accessibility', async () => {
      const { container } = renderLoginForm();
      
      await checkAccessibility(container);
    });

    test('should show proper labels and placeholders', () => {
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);

      expect(usernameInput).toHaveAttribute('placeholder', 'Enter your username');
      expect(passwordInput).toHaveAttribute('placeholder', 'Enter your password');
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    test('should display company logo or title', () => {
      renderLoginForm();

      // Check for logo or title
      const logo = screen.queryByAltText(/logo/i);
      const title = screen.queryByText(/genai cloudops/i);
      
      expect(logo || title).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    test('should allow user to type in username field', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      
      await user.type(usernameInput, 'testuser');
      
      expect(usernameInput).toHaveValue('testuser');
    });

    test('should allow user to type in password field', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const passwordInput = screen.getByLabelText(/password/i);
      
      await user.type(passwordInput, 'testpassword');
      
      expect(passwordInput).toHaveValue('testpassword');
    });

    test('should enable submit button when both fields are filled', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // Initially button might be disabled
      expect(submitButton).toBeDisabled();

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'testpassword');

      expect(submitButton).toBeEnabled();
    });

    test('should show password when show/hide toggle is clicked', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const passwordInput = screen.getByLabelText(/password/i);
      const toggleButton = screen.queryByRole('button', { name: /show password/i });

      if (toggleButton) {
        expect(passwordInput).toHaveAttribute('type', 'password');
        
        await user.click(toggleButton);
        
        expect(passwordInput).toHaveAttribute('type', 'text');
      }
    });
  });

  describe('Form Validation', () => {
    test('should show validation error for empty username', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      const passwordInput = screen.getByLabelText(/password/i);

      await user.type(passwordInput, 'testpassword');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      });
    });

    test('should show validation error for empty password', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(usernameInput, 'testuser');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    test('should show validation error for short password', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, '123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password must be at least/i)).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    test('should handle successful login', async () => {
      const user = userEvent.setup();
      const mockOnSuccess = jest.fn();
      
      renderLoginForm({ onSuccess: mockOnSuccess });

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(usernameInput, 'admin');
      await user.type(passwordInput, 'admin123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    test('should show error message for invalid credentials', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(usernameInput, 'admin');
      await user.type(passwordInput, 'wrongpassword');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    test('should show loading state during login', async () => {
      const user = userEvent.setup();
      
      // Configure server for slow response
      configureServer.slow(1000);
      
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(usernameInput, 'admin');
      await user.type(passwordInput, 'admin123');
      await user.click(submitButton);

      // Should show loading state
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
      expect(submitButton).toHaveTextContent(/signing in/i);
    });

    test('should handle network error gracefully', async () => {
      const user = userEvent.setup();
      
      // Configure server for network error
      configureServer.networkError();
      
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(usernameInput, 'admin');
      await user.type(passwordInput, 'admin123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      
      // Tab to username field
      await user.tab();
      expect(usernameInput).toHaveFocus();

      // Tab to password field
      await user.tab();
      expect(screen.getByLabelText(/password/i)).toHaveFocus();

      // Tab to submit button
      await user.tab();
      expect(screen.getByRole('button', { name: /sign in/i })).toHaveFocus();
    });

    test('should have proper ARIA labels and roles', () => {
      renderLoginForm();

      const form = screen.getByRole('form');
      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      expect(form).toHaveAttribute('aria-label', 'Login form');
      expect(usernameInput).toHaveAttribute('aria-required', 'true');
      expect(passwordInput).toHaveAttribute('aria-required', 'true');
      expect(submitButton).toHaveAttribute('type', 'submit');
    });

    test('should announce form errors to screen readers', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      await user.click(submitButton);

      await waitFor(() => {
        const errorMessage = screen.getByText(/username is required/i);
        expect(errorMessage).toHaveAttribute('role', 'alert');
        expect(errorMessage).toHaveAttribute('aria-live', 'polite');
      });
    });
  });

  describe('Security', () => {
    test('should not expose password in DOM', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const passwordInput = screen.getByLabelText(/password/i);
      
      await user.type(passwordInput, 'secretpassword');

      // Password should be hidden by default
      expect(passwordInput).toHaveAttribute('type', 'password');
      
      // Check that password is not visible in DOM
      expect(screen.queryByText('secretpassword')).not.toBeInTheDocument();
    });

    test('should clear form on unmount', () => {
      const { unmount } = renderLoginForm();
      
      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'testpass' } });

      unmount();

      // After unmount and remount, form should be clean
      renderLoginForm();
      
      expect(screen.getByRole('textbox', { name: /username/i })).toHaveValue('');
      expect(screen.getByLabelText(/password/i)).toHaveValue('');
    });
  });

  describe('Performance', () => {
    test('should render quickly', async () => {
      const { measurePerformance } = await import('../../../test-setup');
      
      const renderTime = await measurePerformance(() => {
        renderLoginForm();
      });

      // Should render within 100ms
      expect(renderTime).toBeLessThan(100);
    });

    test('should handle rapid typing without lag', async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const usernameInput = screen.getByRole('textbox', { name: /username/i });
      
      const startTime = performance.now();
      
      // Type rapidly
      await user.type(usernameInput, 'verylongusername123456789');
      
      const endTime = performance.now();
      
      expect(usernameInput).toHaveValue('verylongusername123456789');
      
      // Should handle rapid typing within reasonable time
      expect(endTime - startTime).toBeLessThan(1000);
    });
  });
}); 