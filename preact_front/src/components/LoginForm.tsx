// src/components/LoginForm.tsx
import { h } from 'preact'; // ← h из 'preact'
import { useState } from 'preact/hooks'; // ← useState из 'preact/hooks'
import { apiClient, setAuthToken } from '../lib/apiClient';
import { API_BASE_URL } from '../config/api'; // Импортируем нашу константу

export const LoginForm = ({ onLogin }: { onLogin: () => void }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('grant_type', 'password'); // ← обязательно

    try {
      const response = await fetch(`${API_BASE_URL}/auth/token`, {
      // const response = await fetch('/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      if (!response.ok) {
        throw new Error('Неверный логин или пароль');
      }

      const data = await response.json();
      await setAuthToken(data.access_token);

      setTimeout(() => {
        onLogin();
      }, 10);

      window.dispatchEvent(new Event('auth-change'));

      onLogin();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <h2 className="text-2xl font-bold text-center mb-6">Вход в систему</h2>
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4"><p className="text-center">{error}</p></div>}
      <div className="form-control">
        <label className="label">
          <span className="label-text">Логин</span>
        </label>
        <input
          type="text"
          placeholder="Введите логин"
          value={username}
          onChange={e => setUsername(e.currentTarget.value)}
          required
          className="input input-bordered w-full"
        />
      </div>
      <div className="form-control">
        <label className="label">
          <span className="label-text">Пароль</span>
        </label>
        <input
          type="password"
          placeholder="Введите пароль"
          value={password}
          onChange={e => setPassword(e.currentTarget.value)}
          required
          className="input input-bordered w-full"
        />
      </div>
      <button 
        type="submit" 
        className="btn btn-primary w-full mt-6"
      >
        Войти
      </button>
      <div className="text-center mt-4">
        <p className="text-sm text-gray-500">Введите свои учетные данные для входа в систему</p>
      </div>
    </form>
  );
};