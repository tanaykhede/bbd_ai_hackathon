import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient, HttpClientModule, HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-login',
  imports: [FormsModule, HttpClientModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {
  username = '';
  password = '';
  isLoading = false;
  // Allows override via window.__env.API_BASE_URL; falls back to localhost:8000 (FastAPI default)
  private apiBase = (window as any)?.__env?.API_BASE_URL || 'http://localhost:8000';

  constructor(private router: Router, private http: HttpClient) {}

  login() {
    if (!this.username || !this.password || this.isLoading) {
      return;
    }
    this.isLoading = true;

    const body = { username: this.username, password: this.password };

    this.http.post<any>(`${this.apiBase}/auth/login`, body).subscribe({
      next: (res) => {
        // Try common token field names
        const token: string | undefined =
          res?.access_token || res?.token || res?.jwt;
        if (!token) {
          throw new Error('Authentication succeeded but no token returned');
        }
        try {
          localStorage.setItem('auth_token', token);
        } catch {
          // If storage fails, continue navigation but warn
          console.warn('Unable to persist auth token to localStorage');
        }
        this.router.navigate(['/chat']);
      },
      error: (err: HttpErrorResponse) => {
        console.error('Login failed', err);
        alert(
          (err?.error && (err.error.detail || err.error.message)) ||
          'Login failed. Please check your username and password.'
        );
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }
}
